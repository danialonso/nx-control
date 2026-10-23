// NX Control service
#include <switch.h>
#include <nlohmann/json.hpp>
#include <cstdio>
#include <set>
#include "common.hpp"
#include "config.hpp"
#include "engine.hpp"
#include "enforcer.hpp"
#include "log.hpp"
#include "store.hpp"
#include "tracker.hpp"

#ifndef NXC_VERSION
#define NXC_VERSION "0.0.0-dev"
#endif

extern "C" {
u32 __nx_applet_type = AppletType_None;
u32 __nx_fs_num_sessions = 1;

#define INNER_HEAP_SIZE 0x100000
size_t nx_inner_heap_size = INNER_HEAP_SIZE;
char   nx_inner_heap[INNER_HEAP_SIZE];

void __libnx_initheap(void) {
    extern char *fake_heap_start;
    extern char *fake_heap_end;
    fake_heap_start = nx_inner_heap;
    fake_heap_end   = nx_inner_heap + nx_inner_heap_size;
}

void __appInit(void) {
    Result rc = smInitialize();
    if (R_FAILED(rc)) diagAbortWithResult(MAKERESULT(Module_Libnx, LibnxError_InitFail_SM));

    if (R_SUCCEEDED(setsysInitialize())) {
        SetSysFirmwareVersion fw;
        if (R_SUCCEEDED(setsysGetFirmwareVersion(&fw)))
            hosversionSet(MAKEHOSVERSION(fw.major, fw.minor, fw.micro));
        setsysExit();
    }

    rc = fsInitialize();
    if (R_FAILED(rc)) diagAbortWithResult(MAKERESULT(Module_Libnx, LibnxError_InitFail_FS));
    fsdevMountSdmc();

    rc = timeInitialize();
    if (R_FAILED(rc)) diagAbortWithResult(rc);
}

void __appExit(void) {
    timeExit();
    fsdevUnmountAll();
    fsExit();
    smExit();
}
}

using namespace nxc;
using nlohmann::json;

namespace {

constexpr u64 kTickNs        = 1'000'000'000ULL;   // main loop period
constexpr u64 kMaxDeltaNs    = 5'000'000'000ULL;   // ignore gaps (sleep mode)
constexpr u64 kSaveEveryNs   = 30'000'000'000ULL;
constexpr u64 kKickCooldown  = 3'000'000'000ULL;

struct Runtime {
    Config config;
    Store store;
    Tracker tracker;
    Enforcer enforcer;

    std::string active_user;
    u64 active_program = 0;
    std::set<int> warned;            // warning thresholds already shown this session
    u64 grace_until = 0;             // steady ns, 0 = no grace running
    u64 last_kick = 0;
    u64 suspended_since = 0;
    PlayState state = PlayState::Idle;
};

void writeState(Runtime &rt, const Foreground &fg, const LocalNow &now) {
    json j;
    j["version"] = NXC_VERSION;
    j["updated_at"] = now.iso;
    j["session"] = {
        {"active", fg.running},
        {"focused", fg.focused},
        {"profile_id", fg.user_id},
        {"program_id", fg.running ? programIdToString(fg.program_id) : ""},
        {"state", stateToString(rt.state)},
    };
    j["profiles"] = json::array();
    for (const auto &p : rt.config.profiles) {
        Evaluation e = evaluate(p, rt.store, now);
        j["profiles"].push_back({
            {"id", p.user_id},
            {"name", p.name},
            {"mode", modeToString(p.mode)},
            {"used_today", rt.store.usedSeconds(p.user_id)},
            {"limit_today", e.limit_today},
            {"remaining_today", e.remaining},
            {"in_allowed_window", e.in_window},
        });
    }
    std::string tmp = std::string(kStatePath) + ".tmp";
    if (FILE *f = std::fopen(tmp.c_str(), "wb")) {
        std::string out = j.dump();
        std::fwrite(out.data(), 1, out.size(), f);
        std::fclose(f);
        remove(kStatePath);
        rename(tmp.c_str(), kStatePath);
    }
}

void enforce(Runtime &rt, const Foreground &fg, const Profile &p, const Evaluation &e, u64 now_ns) {
    if (!e.limited) { rt.state = PlayState::Playing; return; }

    // Warnings (15, 5, 1 min by default)
    if (e.allowed && e.remaining > 0) {
        rt.state = PlayState::Playing;
        for (int w : p.rules.warnings_minutes) {
            if (e.remaining <= static_cast<s64>(w) * 60 && !rt.warned.count(w)) {
                rt.warned.insert(w);
                rt.state = PlayState::Warning;
                log::event("WARNING", "user=%s remaining=%llds", p.user_id.c_str(), (long long)e.remaining);
                // TODO: native notification / overlay toast
            }
        }
        rt.grace_until = 0;
        return;
    }

    // Time is up (or outside window): grace period first
    if (rt.grace_until == 0 && fg.focused) {
        rt.grace_until = now_ns + static_cast<u64>(p.rules.grace_seconds) * 1'000'000'000ULL;
        rt.state = PlayState::Grace;
        log::event("GRACE", "user=%s %ds", p.user_id.c_str(), p.rules.grace_seconds);
        return;
    }
    if (now_ns < rt.grace_until) { rt.state = PlayState::Grace; return; }

    rt.state = e.in_window ? PlayState::Exhausted : PlayState::OutsideWindow;

    // Only press HOME while the game is focused: pressing HOME in the HOME menu resumes the game.
    if (fg.focused && now_ns - rt.last_kick > kKickCooldown) {
        rt.last_kick = now_ns;
        if (rt.suspended_since == 0) rt.suspended_since = now_ns;
        log::event("SUSPEND", "user=%s program=%s", p.user_id.c_str(), programIdToString(fg.program_id).c_str());
        rt.enforcer.sendToHome();
    }

    // Optional hard stop after N minutes suspended
    if (p.rules.close_after_minutes > 0 && rt.suspended_since &&
        now_ns - rt.suspended_since > static_cast<u64>(p.rules.close_after_minutes) * 60'000'000'000ULL) {
        log::event("CLOSE", "user=%s program=%s", p.user_id.c_str(), programIdToString(fg.program_id).c_str());
        rt.enforcer.closeApplication();
        rt.suspended_since = 0;
    }
}

} // namespace

int main(int, char **) {
    ensureDirs();
    log::debug("NX Control %s starting", NXC_VERSION);

    static Runtime rt;
    rt.config.load();
    rt.tracker.init();
    rt.enforcer.init();

    LocalNow now = localNow();
    rt.store.load(now.valid ? now.date : "unknown");

    u64 last_ns = steadyNs();
    u64 last_save = last_ns;
    u64 last_wall = now.posix;
    u64 last_state_write = 0;
    PlayState last_state = PlayState::Idle;
    bool last_focused = false;

    while (true) {
        svcSleepThread(kTickNs);

        u64 now_ns = steadyNs();
        u64 delta = now_ns - last_ns;
        last_ns = now_ns;
        if (delta > kMaxDeltaNs) delta = 0;   // console was asleep

        now = localNow();

        // Clock tamper detection: wall clock moved much more than the monotonic clock.
        if (now.valid && last_wall) {
            s64 wall_delta = static_cast<s64>(now.posix) - static_cast<s64>(last_wall);
            s64 mono_delta = static_cast<s64>(delta / 1'000'000'000ULL);
            if (delta && (wall_delta - mono_delta > 120 || wall_delta - mono_delta < -120))
                log::event("TAMPER", "clock jump %llds", (long long)(wall_delta - mono_delta));
        }
        last_wall = now.posix;

        if (now.valid && now.date != rt.store.date()) rt.store.rollover(now.date);

        Foreground fg = rt.tracker.poll();

        // Session changes
        if (fg.user_id != rt.active_user || fg.program_id != rt.active_program) {
            if (!rt.active_user.empty()) log::event("SESSION_END", "user=%s", rt.active_user.c_str());
            if (fg.running) log::event("SESSION_START", "user=%s program=%s", fg.user_id.c_str(),
                                       programIdToString(fg.program_id).c_str());
            rt.active_user = fg.user_id;
            rt.active_program = fg.program_id;
            rt.warned.clear();
            rt.grace_until = 0;
            rt.suspended_since = 0;
        }

        if (fg.running && fg.focused && !fg.user_id.empty())
            rt.store.add(fg.user_id, fg.program_id, delta);

        rt.state = PlayState::Idle;
        if (fg.running && !fg.user_id.empty()) {
            if (const Profile *p = rt.config.find(fg.user_id)) {
                Evaluation e = evaluate(*p, rt.store, now);
                enforce(rt, fg, *p, e, now_ns);
            } else {
                rt.state = PlayState::Playing;
            }
        }

        if (rt.store.dirty() && now_ns - last_save > kSaveEveryNs) {
            rt.store.save();
            last_save = now_ns;
        }
        // Keep SD writes low: on state change or every 10 s.
        if (rt.state != last_state || fg.focused != last_focused || now_ns - last_state_write > 10'000'000'000ULL) {
            writeState(rt, fg, now);
            last_state = rt.state;
            last_focused = fg.focused;
            last_state_write = now_ns;
        }
    }

    rt.store.save();
    rt.enforcer.exit();
    rt.tracker.exit();
    return 0;
}
