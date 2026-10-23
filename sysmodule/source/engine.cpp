#include "engine.hpp"

namespace nxc {

const char *stateToString(PlayState s) {
    switch (s) {
        case PlayState::Playing:       return "playing";
        case PlayState::Warning:       return "warning";
        case PlayState::Grace:         return "grace";
        case PlayState::Exhausted:     return "exhausted";
        case PlayState::OutsideWindow: return "outside_window";
        case PlayState::Blocked:       return "blocked";
        default:                       return "idle";
    }
}

Evaluation evaluate(const Profile &p, const Store &store, const LocalNow &now) {
    Evaluation e;
    if (p.mode == Mode::Analytics || !now.valid) return e;

    const Rules &r = p.rules;

    // Daily budget
    int minutes = r.daily_minutes[now.weekday];
    if (minutes >= 0) {
        e.limited = true;
        e.limit_today = static_cast<s64>(minutes) * 60 + store.bonusSeconds(p.user_id);
        e.remaining = e.limit_today - static_cast<s64>(store.usedSeconds(p.user_id));
        if (e.remaining < 0) e.remaining = 0;
    }

    // Allowed windows
    if (!r.windows.empty()) {
        e.limited = true;
        e.in_window = false;
        int mod = now.minuteOfDay();
        for (const auto &w : r.windows) {
            if (!(w.days & (1u << now.weekday))) continue;
            if (mod >= w.from && mod < w.to) {
                e.in_window = true;
                s64 ends = static_cast<s64>(w.to - mod) * 60 - now.second;
                if (e.window_ends_in < 0 || ends > e.window_ends_in) e.window_ends_in = ends;
            }
        }
    }

    // The effective remaining time is the smallest of budget and window.
    if (e.window_ends_in >= 0 && (e.remaining < 0 || e.window_ends_in < e.remaining))
        e.remaining = e.window_ends_in;

    e.allowed = e.in_window && (e.remaining != 0);
    return e;
}

} // namespace nxc
