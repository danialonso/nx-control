#include "config.hpp"
#include "common.hpp"
#include "log.hpp"
#include <nlohmann/json.hpp>
#include <cstdio>
#include <cstring>

using nlohmann::json;

namespace nxc {

static const char *kDays[7] = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"};

const char *modeToString(Mode m) {
    switch (m) {
        case Mode::Self:      return "self";
        case Mode::Analytics: return "analytics";
        default:              return "supervised";
    }
}

static Mode modeFromString(const std::string &s) {
    if (s == "self") return Mode::Self;
    if (s == "analytics") return Mode::Analytics;
    return Mode::Supervised;
}

static int parseHHMM(const std::string &s, int fallback) {
    int h = 0, m = 0;
    if (std::sscanf(s.c_str(), "%d:%d", &h, &m) != 2) return fallback;
    return h * 60 + m;
}

static std::string readFile(const char *path) {
    std::string out;
    FILE *f = std::fopen(path, "rb");
    if (!f) return out;
    char buf[1024];
    size_t n;
    while ((n = std::fread(buf, 1, sizeof(buf), f)) > 0) out.append(buf, n);
    std::fclose(f);
    return out;
}

static void parseRules(const json &j, const json &defaults, Rules &r) {
    const json &d = defaults.is_object() ? defaults : json::object();

    if (j.contains("daily_minutes")) {
        const json &dm = j["daily_minutes"];
        for (int i = 0; i < 7; i++) {
            if (dm.is_number_integer()) r.daily_minutes[i] = dm.get<int>();
            else if (dm.is_object() && dm.contains(kDays[i]) && dm[kDays[i]].is_number_integer())
                r.daily_minutes[i] = dm[kDays[i]].get<int>();
        }
    }

    if (j.contains("allowed_windows") && j["allowed_windows"].is_array()) {
        for (const auto &w : j["allowed_windows"]) {
            TimeWindow tw;
            if (w.contains("days") && w["days"].is_array()) {
                tw.days = 0;
                for (const auto &day : w["days"])
                    for (int i = 0; i < 7; i++)
                        if (day.is_string() && day.get<std::string>() == kDays[i]) tw.days |= (1u << i);
            }
            tw.from = parseHHMM(w.value("from", std::string("00:00")), 0);
            tw.to   = parseHHMM(w.value("to", std::string("24:00")), 24 * 60);
            r.windows.push_back(tw);
        }
    }

    const json &warn = j.contains("warnings_minutes") ? j["warnings_minutes"]
                     : (d.contains("warnings_minutes") ? d["warnings_minutes"] : json());
    if (warn.is_array()) {
        r.warnings_minutes.clear();
        for (const auto &w : warn) if (w.is_number_integer()) r.warnings_minutes.push_back(w.get<int>());
    }
    r.grace_seconds       = j.value("grace_seconds", d.value("grace_seconds", 60));
    r.close_after_minutes = j.value("close_after_minutes", d.value("close_after_minutes", 0));
}

bool Config::load() {
    profiles.clear();
    std::string text = readFile(kConfigPath);
    if (text.empty()) {
        log::debug("config.json not found, using defaults");
        return false;
    }
    json j = json::parse(text, nullptr, false);
    if (j.is_discarded() || !j.is_object()) {
        log::debug("config.json is not valid JSON, using defaults");
        return false;
    }

    pin_hash = j.value("pin_hash", std::string());
    if (j.contains("network") && j["network"].is_object()) {
        network_enabled = j["network"].value("enabled", true);
        network_port    = j["network"].value("port", 8460);
    }
    json defaults = j.contains("defaults") ? j["defaults"] : json::object();

    if (j.contains("profiles") && j["profiles"].is_array()) {
        for (const auto &p : j["profiles"]) {
            Profile prof;
            prof.user_id = p.value("user_id", std::string());
            prof.name    = p.value("name", std::string());
            prof.mode    = modeFromString(p.value("mode", std::string("supervised")));
            parseRules(p.contains("rules") ? p["rules"] : json::object(), defaults, prof.rules);
            if (!prof.user_id.empty()) profiles.push_back(std::move(prof));
        }
    }
    log::debug("config loaded: %u profile(s)", (unsigned)profiles.size());
    return true;
}

const Profile *Config::find(const std::string &user_id) const {
    for (const auto &p : profiles)
        if (strcasecmp(p.user_id.c_str(), user_id.c_str()) == 0) return &p;
    return nullptr;
}

} // namespace nxc
