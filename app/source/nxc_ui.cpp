#include "nxc_ui.hpp"
#include "nxc_data.hpp"
#include "nxc_i18n.hpp"
#if __has_include("nxc_version.hpp")
#include "nxc_version.hpp"
#endif
#include <cstdio>
#include <memory>

#ifndef NXC_VERSION
#define NXC_VERSION "dev"
#endif

using nlohmann::json;

namespace nxc::ui {

static bool g_unlocked = false;
bool isUnlocked() { return g_unlocked; }
void setUnlocked(bool unlocked) { g_unlocked = unlocked; }

static const char* kDays[7] = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"};

// ---------------------------------------------------------------- helpers

static void persist() {
    if (!ConfigStore::get().save()) brls::Application::notify(tr("save_error"));
}

static brls::Header* header(const std::string& title, const std::string& subtitle = "") {
    auto* h = new brls::Header();
    h->setTitle(title);
    if (!subtitle.empty()) h->setSubtitle(subtitle);
    return h;
}

static brls::Label* note(const std::string& text) {
    auto* l = new brls::Label();
    l->setText(text);
    l->setFontSize(16);
    l->setMarginTop(8);
    l->setMarginBottom(16);
    return l;
}

static brls::ScrollingFrame* scrollable(brls::Box* content) {
    auto* scroll = new brls::ScrollingFrame();
    scroll->setContentView(content);
    return scroll;
}

static brls::Box* column() {
    auto* box = new brls::Box(brls::Axis::COLUMN);
    box->setPadding(30, 60, 30, 60);
    return box;
}

static bool isDigits(const std::string& s) {
    if (s.empty()) return false;
    for (char c : s) if (c < '0' || c > '9') return false;
    return true;
}

static std::string modeLabel(const std::string& mode) {
    if (mode == "supervised") return tr("mode/supervised");
    if (mode == "self") return tr("mode/self");
    if (mode == "analytics") return tr("mode/analytics");
    return tr("mode/none");
}

// Minutes options for the daily selectors. -1 = unlimited.
static std::vector<int> minuteOptions(int current) {
    std::vector<int> v = {-1, 0, 15, 30, 45, 60, 75, 90, 105, 120, 150, 180, 210, 240, 300, 360};
    bool found = false;
    for (int m : v) found |= (m == current);
    if (!found) v.push_back(current);
    return v;
}

static std::string minutesLabel(int m) {
    if (m < 0) return tr("unlimited");
    if (m == 0) return tr("min/none");
    char buf[32];
    if (m >= 60 && m % 60 == 0) std::snprintf(buf, sizeof(buf), "%d h", m / 60);
    else if (m > 60) std::snprintf(buf, sizeof(buf), "%d h %02d min", m / 60, m % 60);
    else std::snprintf(buf, sizeof(buf), "%d min", m);
    return buf;
}

static std::string hhmm(int minutes) {
    char buf[8];
    std::snprintf(buf, sizeof(buf), "%02d:%02d", minutes / 60, minutes % 60);
    return buf;
}

static int parseHHMM(const std::string& s, int fallback) {
    int h = 0, m = 0;
    if (std::sscanf(s.c_str(), "%d:%d", &h, &m) != 2) return fallback;
    return h * 60 + m;
}

// ---------------------------------------------------------------- PIN

static void createPin(std::function<void()> done) {
    auto* ime = brls::Application::getImeManager();
    ime->openForText([done](std::string first) {
        if (!isDigits(first) || first.size() < 4 || first.size() > 8) {
            brls::Application::notify(tr("pin/invalid"));
            return;
        }
        brls::Application::getImeManager()->openForText([first, done](std::string second) {
            if (first != second) {
                brls::Application::notify(tr("pin/mismatch"));
                return;
            }
            ConfigStore::get().setPin(first);
            persist();
            g_unlocked = true;
            brls::Application::notify(tr("pin/set"));
            if (done) done();
        }, tr("pin/repeat"), "", 8, "", brls::KEYBOARD_DISABLE_SPACE);
    }, tr("pin/new"), "", 8, "", brls::KEYBOARD_DISABLE_SPACE);
}

void askPin(std::function<void()> onSuccess) {
    brls::Application::getImeManager()->openForText([onSuccess](std::string pin) {
        if (ConfigStore::get().checkPin(pin)) {
            g_unlocked = true;
            brls::Application::notify(tr("pin/unlocked"));
            if (onSuccess) onSuccess();
        } else {
            brls::Application::notify(tr("pin/wrong"));
        }
    }, tr("pin/enter"), "", 8, "", brls::KEYBOARD_DISABLE_SPACE);
}

// Shown in protected tabs while locked.
static brls::View* lockedView() {
    auto* box = column();
    box->addView(note(tr("pin/locked")));
    auto* unlock = new brls::DetailCell();
    unlock->setText(tr("pin/unlock"));
    unlock->registerClickAction([](brls::View*) {
        askPin([] {
            // Rebuild the main screen so every tab shows its unlocked content.
            brls::Application::popActivity(brls::TransitionAnimation::NONE, [] { showMain(); });
        });
        return true;
    });
    box->addView(unlock);
    return scrollable(box);
}

// ---------------------------------------------------------------- Today tab

static std::string stateLabel(const std::string& s) {
    std::string key = "state/" + s;
    const std::string& t = tr(key.c_str());
    return t == "?" ? s : t;
}

static brls::View* todayTab() {
    auto* box = column();
    json state = readState();
    if (state.is_discarded() || !state.is_object()) {
        box->addView(note(tr("today/no_service")));
        return scrollable(box);
    }

    const json& session = state.contains("session") ? state["session"] : json::object();
    std::string activeProfile = session.value("profile_id", std::string());

    auto* now = new brls::DetailCell();
    now->setText(tr("today/now"));
    now->setDetailText(session.value("active", false) ? tr("today/playing") : tr("today/no_game"));
    box->addView(now);

    if (!state.contains("profiles") || state["profiles"].empty()) {
        box->addView(note(tr("today/no_profiles")));
        return scrollable(box);
    }

    for (const auto& p : state["profiles"]) {
        std::string id = p.value("id", std::string());
        box->addView(header(p.value("name", id), modeLabel(p.value("mode", std::string()))));

        auto* played = new brls::DetailCell();
        played->setText(tr("today/played"));
        played->setDetailText(formatDuration(p.value("used_today", 0LL)));
        box->addView(played);

        long long remaining = p.value("remaining_today", -1LL);
        auto* rem = new brls::DetailCell();
        rem->setText(tr("today/remaining"));
        rem->setDetailText(remaining < 0 ? tr("unlimited") : formatDuration(remaining));
        box->addView(rem);

        if (id == activeProfile) {
            auto* st = new brls::DetailCell();
            st->setText(tr("today/status"));
            st->setDetailText(stateLabel(session.value("state", std::string("idle"))));
            box->addView(st);
        }
    }
    return scrollable(box);
}

// ---------------------------------------------------------------- Profile editor

struct EditorState {
    ConsoleUser user;
};

static json& rulesOf(const ConsoleUser& u) {
    json& p = ConfigStore::get().ensureProfile(u.id, u.name);
    if (!p.contains("rules") || !p["rules"].is_object()) p["rules"] = json::object();
    return p["rules"];
}

static int dailyMinutes(const ConsoleUser& u, int day) {
    json* p = ConfigStore::get().findProfile(u.id);
    if (!p || !p->contains("rules")) return -1;
    const json& r = (*p)["rules"];
    if (!r.contains("daily_minutes")) return -1;
    const json& dm = r["daily_minutes"];
    if (dm.is_number_integer()) return dm.get<int>();
    if (dm.is_object() && dm.contains(kDays[day]) && dm[kDays[day]].is_number_integer())
        return dm[kDays[day]].get<int>();
    return -1;
}

static void setDailyMinutes(const ConsoleUser& u, int day, int minutes) {
    json& r = rulesOf(u);
    if (!r.contains("daily_minutes") || !r["daily_minutes"].is_object()) {
        json obj = json::object();
        int all = r.contains("daily_minutes") && r["daily_minutes"].is_number_integer() ? r["daily_minutes"].get<int>() : -1;
        for (const char* d : kDays) obj[d] = all;
        r["daily_minutes"] = obj;
    }
    r["daily_minutes"][kDays[day]] = minutes;
}

struct Windows {
    bool enabled = false;
    int wdFrom = 17 * 60, wdTo = 21 * 60, weFrom = 10 * 60, weTo = 21 * 60;
};

static Windows readWindows(const ConsoleUser& u) {
    Windows w;
    json* p = ConfigStore::get().findProfile(u.id);
    if (!p || !p->contains("rules") || !(*p)["rules"].contains("allowed_windows")) return w;
    for (const auto& win : (*p)["rules"]["allowed_windows"]) {
        w.enabled = true;
        bool weekend = false;
        if (win.contains("days"))
            for (const auto& d : win["days"])
                if (d == "sat" || d == "sun") weekend = true;
        int from = parseHHMM(win.value("from", std::string("00:00")), 0);
        int to = parseHHMM(win.value("to", std::string("24:00")), 24 * 60);
        if (weekend) { w.weFrom = from; w.weTo = to; }
        else { w.wdFrom = from; w.wdTo = to; }
    }
    return w;
}

static void writeWindows(const ConsoleUser& u, const Windows& w) {
    json& r = rulesOf(u);
    if (!w.enabled) {
        r.erase("allowed_windows");
        return;
    }
    r["allowed_windows"] = json::array({
        {{"days", {"mon", "tue", "wed", "thu", "fri"}}, {"from", hhmm(w.wdFrom)}, {"to", hhmm(w.wdTo)}},
        {{"days", {"sat", "sun"}}, {"from", hhmm(w.weFrom)}, {"to", hhmm(w.weTo)}},
    });
}

static brls::SelectorCell* timeSelector(const std::string& title, int value, std::function<void(int)> onChange) {
    std::vector<std::string> labels;
    for (int m = 0; m <= 24 * 60; m += 30) labels.push_back(hhmm(m));
    auto* cell = new brls::SelectorCell();
    cell->init(title, labels, value / 30, [onChange](int sel) { onChange(sel * 30); });
    return cell;
}

static void openProfileEditor(const ConsoleUser& user) {
    auto st = std::make_shared<EditorState>();
    st->user = user;

    auto* box = column();

    // Mode
    json* existing = ConfigStore::get().findProfile(user.id);
    std::string mode = existing ? existing->value("mode", std::string("supervised")) : "none";
    std::vector<std::string> modes = {"none", "supervised", "self", "analytics"};
    int modeIdx = 0;
    for (size_t i = 0; i < modes.size(); i++) if (modes[i] == mode) modeIdx = (int)i;

    auto* modeCell = new brls::SelectorCell();
    modeCell->init(tr("mode/title"),
        {tr("mode/none"), tr("mode/supervised"), tr("mode/self"), tr("mode/analytics")}, modeIdx,
        [st, modes](int sel) {
            if (modes[sel] == "none") {
                ConfigStore::get().removeProfile(st->user.id);
            } else {
                json& p = ConfigStore::get().ensureProfile(st->user.id, st->user.name);
                p["mode"] = modes[sel];
            }
            persist();
        });
    box->addView(modeCell);

    // Daily time
    box->addView(header(tr("daily/header")));
    std::vector<brls::SelectorCell*> dayCells;
    for (int d = 0; d < 7; d++) {
        int current = dailyMinutes(user, d);
        auto options = minuteOptions(current);
        std::vector<std::string> labels;
        int idx = 0;
        for (size_t i = 0; i < options.size(); i++) {
            labels.push_back(minutesLabel(options[i]));
            if (options[i] == current) idx = (int)i;
        }
        auto* cell = new brls::SelectorCell();
        std::string dayKey = "day/" + std::to_string(d);
        cell->init(tr(dayKey.c_str()), labels, idx, [st, d, options](int sel) {
            setDailyMinutes(st->user, d, options[sel]);
            persist();
        });
        dayCells.push_back(cell);
        box->addView(cell);
    }
    auto* applyAll = new brls::DetailCell();
    applyAll->setText(tr("daily/apply_all"));
    applyAll->registerClickAction([st, dayCells](brls::View*) {
        int monday = dailyMinutes(st->user, 0);
        for (int d = 1; d < 7; d++) {
            setDailyMinutes(st->user, d, monday);
            dayCells[d]->setSelection(dayCells[0]->getSelection(), true);
        }
        persist();
        brls::Application::notify(tr("saved"));
        return true;
    });
    box->addView(applyAll);

    // Allowed hours
    box->addView(header(tr("hours/header")));
    auto win = std::make_shared<Windows>(readWindows(user));
    auto* enabled = new brls::BooleanCell();
    enabled->init(tr("hours/enabled"), win->enabled, [st, win](bool on) {
        win->enabled = on;
        writeWindows(st->user, *win);
        persist();
    });
    box->addView(enabled);
    auto save = [st, win] { if (win->enabled) { writeWindows(st->user, *win); persist(); } };
    box->addView(timeSelector(tr("hours/wd_from"), win->wdFrom, [win, save](int v) { win->wdFrom = v; save(); }));
    box->addView(timeSelector(tr("hours/wd_to"), win->wdTo, [win, save](int v) { win->wdTo = v; save(); }));
    box->addView(timeSelector(tr("hours/we_from"), win->weFrom, [win, save](int v) { win->weFrom = v; save(); }));
    box->addView(timeSelector(tr("hours/we_to"), win->weTo, [win, save](int v) { win->weTo = v; save(); }));

    // When time is up
    box->addView(header(tr("end/header")));
    json* prof = ConfigStore::get().findProfile(user.id);
    int grace = prof && prof->contains("rules") ? (*prof)["rules"].value("grace_seconds", 60) : 60;
    int closeAfter = prof && prof->contains("rules") ? (*prof)["rules"].value("close_after_minutes", 0) : 0;

    std::vector<int> graceOpts = {0, 30, 60, 120, 300};
    int gIdx = 2;
    std::vector<std::string> gLabels;
    for (size_t i = 0; i < graceOpts.size(); i++) {
        gLabels.push_back(graceOpts[i] < 60 ? std::to_string(graceOpts[i]) + " s" : std::to_string(graceOpts[i] / 60) + " min");
        if (graceOpts[i] == grace) gIdx = (int)i;
    }
    auto* graceCell = new brls::SelectorCell();
    graceCell->init(tr("end/grace"), gLabels, gIdx, [st, graceOpts](int sel) {
        rulesOf(st->user)["grace_seconds"] = graceOpts[sel];
        persist();
    });
    box->addView(graceCell);

    std::vector<int> closeOpts = {0, 5, 10, 15, 30, 60};
    int cIdx = 0;
    std::vector<std::string> cLabels;
    for (size_t i = 0; i < closeOpts.size(); i++) {
        cLabels.push_back(closeOpts[i] == 0 ? tr("end/never") : std::to_string(closeOpts[i]) + " min");
        if (closeOpts[i] == closeAfter) cIdx = (int)i;
    }
    auto* closeCell = new brls::SelectorCell();
    closeCell->init(tr("end/close"), cLabels, cIdx, [st, closeOpts](int sel) {
        rulesOf(st->user)["close_after_minutes"] = closeOpts[sel];
        persist();
    });
    box->addView(closeCell);
    box->addView(note(tr("end/note")));

    auto* frame = new brls::AppletFrame(scrollable(box));
    frame->setTitle(user.name);
    brls::Application::pushActivity(new brls::Activity(frame));
}

// ---------------------------------------------------------------- Profiles tab

static brls::View* profilesTab() {
    if (!g_unlocked) return lockedView();
    auto* box = column();
    box->addView(header(tr("profiles/header"), tr("profiles/sub")));
    for (const auto& user : listConsoleUsers()) {
        auto* cell = new brls::DetailCell();
        cell->setText(user.name);
        json* p = ConfigStore::get().findProfile(user.id);
        cell->setDetailText(modeLabel(p ? p->value("mode", std::string("supervised")) : "none"));
        cell->registerClickAction([user](brls::View*) {
            openProfileEditor(user);
            return true;
        });
        box->addView(cell);
    }
    return scrollable(box);
}

// ---------------------------------------------------------------- Settings tab

static brls::View* settingsTab() {
    if (!g_unlocked) return lockedView();
    auto* box = column();
    ConfigStore& cfg = ConfigStore::get();

    box->addView(header(tr("pin/header")));
    auto* pin = new brls::DetailCell();
    pin->setText(cfg.hasPin() ? tr("pin/change") : tr("pin/create"));
    pin->registerClickAction([](brls::View*) {
        createPin(nullptr);
        return true;
    });
    box->addView(pin);

    box->addView(header(tr("net/header")));
    bool netOn = cfg.root()["network"].value("enabled", true);
    auto* net = new brls::BooleanCell();
    net->init(tr("net/enabled"), netOn, [](bool on) {
        ConfigStore::get().root()["network"]["enabled"] = on;
        persist();
    });
    box->addView(net);
    box->addView(note(tr("net/note")));

    box->addView(header(tr("about/header")));
    auto* ver = new brls::DetailCell();
    ver->setText(tr("about/version"));
    ver->setDetailText(NXC_VERSION);
    box->addView(ver);

    return scrollable(box);
}

// ---------------------------------------------------------------- Main

void showMain() {
    auto* tabs = new brls::TabFrame();
    tabs->addTab(tr("tab/today"), [] { return todayTab(); });
    tabs->addSeparator();
    tabs->addTab(tr("tab/profiles"), [] { return profilesTab(); });
    tabs->addTab(tr("tab/settings"), [] { return settingsTab(); });

    auto* frame = new brls::AppletFrame(tabs);
    frame->setTitle(tr("app/title"));
    brls::Application::pushActivity(new brls::Activity(frame));
}

void showWelcome() {
    auto* dialog = new brls::Dialog(tr("welcome/text"));
    dialog->addButton(tr("welcome/later"), [] {});
    dialog->addButton(tr("pin/create"), [] {
        brls::sync([] { createPin(nullptr); });
    });
    dialog->open();
}

} // namespace nxc::ui
