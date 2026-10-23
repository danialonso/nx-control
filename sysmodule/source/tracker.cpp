#include "tracker.hpp"
#include "common.hpp"
#include "log.hpp"

namespace nxc {

// pdm stores the program id split in two u32. The order is validated on hardware:
// we accept both until confirmed.
static bool programMatches(const u32 parts[2], u64 program_id) {
    u64 hi_lo = (static_cast<u64>(parts[0]) << 32) | parts[1];
    u64 lo_hi = (static_cast<u64>(parts[1]) << 32) | parts[0];
    return hi_lo == program_id || lo_hi == program_id;
}

Result Tracker::init() {
    Result rc = pmdmntInitialize();
    if (R_FAILED(rc)) { log::debug("pmdmnt init failed 0x%x", rc); return rc; }
    rc = pminfoInitialize();
    if (R_FAILED(rc)) { log::debug("pminfo init failed 0x%x", rc); return rc; }
    rc = accountInitialize(AccountServiceType_System);
    if (R_FAILED(rc)) { log::debug("account init failed 0x%x", rc); return rc; }

    pdm_ok_ = R_SUCCEEDED(pdmqryInitialize());
    if (pdm_ok_) {
        s32 total = 0, start = 0, end = 0;
        if (R_SUCCEEDED(pdmqryGetAvailablePlayEventRange(&total, &start, &end)))
            next_event_ = end + 1;   // only new events from now on
    } else {
        log::debug("pdm:qry unavailable, focus detection disabled");
    }
    return 0;
}

void Tracker::exit() {
    if (pdm_ok_) pdmqryExit();
    accountExit();
    pminfoExit();
    pmdmntExit();
}

void Tracker::readFocusEvents() {
    if (!pdm_ok_ || next_event_ < 0) return;
    PdmPlayEvent events[16];
    for (int guard = 0; guard < 8; guard++) {
        s32 count = 0;
        if (R_FAILED(pdmqryQueryPlayEvent(next_event_, events, 16, &count)) || count <= 0) break;
        for (s32 i = 0; i < count; i++) {
            const PdmPlayEvent &e = events[i];
            if (e.play_event_type != PdmPlayEventType_Applet) continue;
            if (!programMatches(e.event_data.applet.program_id, current_program_)) continue;
            switch (e.event_data.applet.event_type) {
                case PdmAppletEventType_Launch:
                case PdmAppletEventType_InFocus:
                    focused_ = true; break;
                case PdmAppletEventType_OutOfFocus:
                case PdmAppletEventType_OutOfFocus4:
                case PdmAppletEventType_Exit:
                case PdmAppletEventType_Exit5:
                case PdmAppletEventType_Exit6:
                    focused_ = false; break;
                default: break;
            }
        }
        next_event_ += count;
        if (count < 16) break;
    }
}

Foreground Tracker::poll() {
    Foreground fg;
    u64 pid = 0;
    if (R_FAILED(pmdmntGetApplicationProcessId(&pid)) || pid == 0) {
        current_pid_ = 0; current_program_ = 0; focused_ = false; user_.clear();
        return fg;
    }

    if (pid != current_pid_) {
        // New application: assume it is focused (it was just launched from HOME).
        current_pid_ = pid;
        current_program_ = 0;
        pminfoGetProgramId(&current_program_, pid);
        focused_ = true;
        AccountUid uid = {};
        user_ = R_SUCCEEDED(accountGetLastOpenedUser(&uid)) && accountUidIsValid(&uid) ? uidToString(uid) : "";
        log::debug("application %s started by user %s",
                   programIdToString(current_program_).c_str(), user_.c_str());
    }

    // The user can be picked after the game starts (or the last opened user may be stale
    // right after boot), so keep it up to date while the game is running.
    if (now_check_user_++ % 3 == 0) {
        AccountUid uid = {};
        if (R_SUCCEEDED(accountGetLastOpenedUser(&uid)) && accountUidIsValid(&uid)) {
            std::string u = uidToString(uid);
            if (u != user_) {
                log::debug("active user changed to %s", u.c_str());
                user_ = u;
            }
        }
    }

    readFocusEvents();

    fg.running    = true;
    fg.focused    = pdm_ok_ ? focused_ : true;
    fg.program_id = current_program_;
    fg.user_id    = user_;
    return fg;
}

} // namespace nxc
