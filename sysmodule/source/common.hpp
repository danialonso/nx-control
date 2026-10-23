#pragma once
#include <switch.h>
#include <string>

namespace nxc {

constexpr const char *kBaseDir    = "sdmc:/config/nxcontrol";
constexpr const char *kConfigPath = "sdmc:/config/nxcontrol/config.json";
constexpr const char *kStatePath  = "sdmc:/config/nxcontrol/state.json";
constexpr const char *kUsageDir   = "sdmc:/config/nxcontrol/usage";
constexpr const char *kTodayPath  = "sdmc:/config/nxcontrol/usage/today.json";
constexpr const char *kHistory    = "sdmc:/config/nxcontrol/usage/history.csv";
constexpr const char *kEventsLog  = "sdmc:/config/nxcontrol/events.log";
constexpr const char *kDebugLog   = "sdmc:/config/nxcontrol/log.txt";

// Monotonic time in nanoseconds (does not depend on the wall clock).
inline u64 steadyNs() { return armTicksToNs(armGetSystemTick()); }

// Console account UID as 32 hex chars.
std::string uidToString(const AccountUid &uid);
std::string programIdToString(u64 program_id);

struct LocalNow {
    bool valid = false;
    int year = 0, month = 0, day = 0, hour = 0, minute = 0, second = 0;
    int weekday = 0;          // 0 = Monday ... 6 = Sunday
    std::string date;         // YYYY-MM-DD
    std::string iso;          // YYYY-MM-DDTHH:MM:SS
    u64 posix = 0;            // wall clock seconds (user clock)
    int minuteOfDay() const { return hour * 60 + minute; }
};
LocalNow localNow();

void ensureDirs();

} // namespace nxc
