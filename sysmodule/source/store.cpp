#include "store.hpp"
#include "common.hpp"
#include "log.hpp"
#include <nlohmann/json.hpp>
#include <cstdio>
#include <cstdlib>

using nlohmann::json;

namespace nxc {

void Store::load(const std::string &today) {
    date_ = today;
    ns_.clear();
    bonus_.clear();

    FILE *f = std::fopen(kTodayPath, "rb");
    if (!f) return;
    std::string text;
    char buf[1024]; size_t n;
    while ((n = std::fread(buf, 1, sizeof(buf), f)) > 0) text.append(buf, n);
    std::fclose(f);

    json j = json::parse(text, nullptr, false);
    if (j.is_discarded() || !j.is_object()) return;
    std::string saved_date = j.value("date", std::string());

    if (j.contains("users") && j["users"].is_object()) {
        for (auto &[user, u] : j["users"].items()) {
            if (u.contains("games") && u["games"].is_object())
                for (auto &[pid, secs] : u["games"].items())
                    ns_[user][std::strtoull(pid.c_str(), nullptr, 16)] = secs.get<u64>() * 1'000'000'000ULL;
            bonus_[user] = u.value("bonus", (s64)0);
        }
    }

    if (!saved_date.empty() && saved_date != today) {
        // Console was off across midnight: archive the old day.
        date_ = saved_date;
        rollover(today);
    }
}

void Store::add(const std::string &user, u64 program_id, u64 ns) {
    ns_[user][program_id] += ns;
    dirty_ = true;
}

void Store::grant(const std::string &user, s64 seconds) {
    bonus_[user] += seconds;
    dirty_ = true;
}

u64 Store::usedSeconds(const std::string &user) const {
    auto it = ns_.find(user);
    if (it == ns_.end()) return 0;
    u64 total = 0;
    for (const auto &[pid, ns] : it->second) total += ns;
    return total / 1'000'000'000ULL;
}

s64 Store::bonusSeconds(const std::string &user) const {
    auto it = bonus_.find(user);
    return it == bonus_.end() ? 0 : it->second;
}

void Store::rollover(const std::string &new_date) {
    FILE *f = std::fopen(kHistory, "a");
    if (f) {
        for (const auto &[user, games] : ns_)
            for (const auto &[pid, ns] : games)
                std::fprintf(f, "%s,%s,%s,%llu\n", date_.c_str(), user.c_str(),
                             programIdToString(pid).c_str(), (unsigned long long)(ns / 1'000'000'000ULL));
        std::fclose(f);
    }
    log::event("DAY", "closed %s", date_.c_str());
    date_ = new_date;
    ns_.clear();
    bonus_.clear();
    dirty_ = true;
    save();
}

void Store::save() {
    json j;
    j["date"] = date_;
    j["users"] = json::object();
    for (const auto &[user, games] : ns_) {
        json g = json::object();
        for (const auto &[pid, ns] : games) g[programIdToString(pid)] = ns / 1'000'000'000ULL;
        j["users"][user]["games"] = g;
    }
    for (const auto &[user, b] : bonus_) j["users"][user]["bonus"] = b;

    std::string tmp = std::string(kTodayPath) + ".tmp";
    FILE *f = std::fopen(tmp.c_str(), "wb");
    if (!f) return;
    std::string out = j.dump();
    std::fwrite(out.data(), 1, out.size(), f);
    std::fclose(f);
    remove(kTodayPath);
    rename(tmp.c_str(), kTodayPath);
    dirty_ = false;
}

} // namespace nxc
