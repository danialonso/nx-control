#include "common.hpp"
#include <cstdio>
#include <sys/stat.h>

namespace nxc {

std::string uidToString(const AccountUid &uid) {
    char buf[33];
    std::snprintf(buf, sizeof(buf), "%016lx%016lx", uid.uid[0], uid.uid[1]);
    return buf;
}

std::string programIdToString(u64 program_id) {
    char buf[17];
    std::snprintf(buf, sizeof(buf), "%016lX", program_id);
    return buf;
}

LocalNow localNow() {
    LocalNow n;
    u64 ts = 0;
    if (R_FAILED(timeGetCurrentTime(TimeType_Default, &ts))) return n;
    TimeCalendarTime cal = {};
    TimeCalendarAdditionalInfo info = {};
    if (R_FAILED(timeToCalendarTimeWithMyRule(ts, &cal, &info))) return n;
    n.valid   = true;
    n.posix   = ts;
    n.year    = cal.year;
    n.month   = cal.month;
    n.day     = cal.day;
    n.hour    = cal.hour;
    n.minute  = cal.minute;
    n.second  = cal.second;
    n.weekday = (static_cast<int>(info.wday) + 6) % 7; // libnx: 0 = Sunday
    char d[16], iso[24];
    std::snprintf(d, sizeof(d), "%04d-%02d-%02d", n.year, n.month, n.day);
    std::snprintf(iso, sizeof(iso), "%sT%02d:%02d:%02d", d, n.hour, n.minute, n.second);
    n.date = d;
    n.iso  = iso;
    return n;
}

void ensureDirs() {
    mkdir("sdmc:/config", 0777);
    mkdir(kBaseDir, 0777);
    mkdir(kUsageDir, 0777);
}

} // namespace nxc
