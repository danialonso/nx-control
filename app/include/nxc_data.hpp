#pragma once
#include <nlohmann/json.hpp>
#include <string>
#include <vector>

namespace nxc {

constexpr const char* kConfigPath = "sdmc:/config/nxcontrol/config.json";
constexpr const char* kStatePath  = "sdmc:/config/nxcontrol/state.json";

struct ConsoleUser {
    std::string id;     // 32 hex chars, same format as the service
    std::string name;
};

std::vector<ConsoleUser> listConsoleUsers();

// Reads/writes config.json. Unknown fields are preserved.
class ConfigStore {
  public:
    static ConfigStore& get();

    bool load();
    bool save();

    nlohmann::json& root() { return j_; }
    nlohmann::json* findProfile(const std::string& user_id);
    nlohmann::json& ensureProfile(const std::string& user_id, const std::string& name);
    void removeProfile(const std::string& user_id);

    bool hasPin();
    bool checkPin(const std::string& pin);
    void setPin(const std::string& pin);

  private:
    nlohmann::json j_;
};

nlohmann::json readState();
std::string formatDuration(long long seconds);

} // namespace nxc
