#pragma once
#include "config.hpp"
#include "store.hpp"
#include "common.hpp"
#include <string>

namespace nxc {

enum class PlayState { Idle, Playing, Warning, Grace, Exhausted, OutsideWindow, Blocked };
const char *stateToString(PlayState s);

struct Evaluation {
    bool limited = false;          // false = no limits apply (analytics / unlimited)
    s64  limit_today = -1;         // seconds, -1 = unlimited
    s64  remaining = -1;           // seconds, -1 = unlimited
    bool in_window = true;
    s64  window_ends_in = -1;      // seconds until the current window closes, -1 = n/a
    bool allowed = true;           // may play right now
};

// Pure rule evaluation: no side effects.
Evaluation evaluate(const Profile &p, const Store &store, const LocalNow &now);

} // namespace nxc
