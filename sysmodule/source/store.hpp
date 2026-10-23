#pragma once
#include <switch.h>
#include <map>
#include <string>

namespace nxc {

// Usage counters for the current day, persisted to the SD card.
class Store {
public:
    void load(const std::string &today);
    void add(const std::string &user, u64 program_id, u64 ns);
    void grant(const std::string &user, s64 seconds);
    // Closes the current day (appends it to history.csv) and starts a new one.
    void rollover(const std::string &new_date);
    void save();

    u64 usedSeconds(const std::string &user) const;
    s64 bonusSeconds(const std::string &user) const;
    const std::string &date() const { return date_; }
    bool dirty() const { return dirty_; }

private:
    std::string date_;
    std::map<std::string, std::map<u64, u64>> ns_;   // user -> program -> ns
    std::map<std::string, s64> bonus_;               // user -> granted seconds
    bool dirty_ = false;
};

} // namespace nxc
