#pragma once
#include <string>
#include <vector>

namespace nxc {

enum class Mode { Supervised, Self, Analytics };

struct TimeWindow {
    unsigned days = 0x7F;   // bit 0 = Monday ... bit 6 = Sunday
    int from = 0;           // minutes since midnight
    int to   = 24 * 60;     // exclusive
};

struct Rules {
    int daily_minutes[7] = {-1, -1, -1, -1, -1, -1, -1};  // -1 = unlimited, index 0 = Monday
    std::vector<TimeWindow> windows;                      // empty = any time
    std::vector<int> warnings_minutes = {15, 5, 1};
    int grace_seconds = 60;
    int close_after_minutes = 0;                          // 0 = never close
};

struct Profile {
    std::string user_id;
    std::string name;
    Mode mode = Mode::Supervised;
    Rules rules;
};

struct Config {
    bool network_enabled = true;
    int  network_port = 8460;
    std::string pin_hash;
    std::vector<Profile> profiles;

    bool load();
    const Profile *find(const std::string &user_id) const;
};

const char *modeToString(Mode m);

} // namespace nxc
