#include "nxc_data.hpp"
#include <switch.h>
#include <cstdio>
#include <cstring>
#include <sys/stat.h>

using nlohmann::json;

namespace nxc {

static std::string readFile(const char* path) {
    std::string out;
    FILE* f = std::fopen(path, "rb");
    if (!f) return out;
    char buf[2048];
    size_t n;
    while ((n = std::fread(buf, 1, sizeof(buf), f)) > 0) out.append(buf, n);
    std::fclose(f);
    return out;
}

std::vector<ConsoleUser> listConsoleUsers() {
    std::vector<ConsoleUser> users;
    if (R_FAILED(accountInitialize(AccountServiceType_Application))) return users;
    AccountUid uids[ACC_USER_LIST_SIZE];
    s32 count = 0;
    if (R_SUCCEEDED(accountListAllUsers(uids, ACC_USER_LIST_SIZE, &count))) {
        for (s32 i = 0; i < count; i++) {
            ConsoleUser u;
            char id[33];
            std::snprintf(id, sizeof(id), "%016lx%016lx", uids[i].uid[0], uids[i].uid[1]);
            u.id = id;
            AccountProfile profile;
            AccountProfileBase base = {};
            if (R_SUCCEEDED(accountGetProfile(&profile, uids[i]))) {
                accountProfileGet(&profile, nullptr, &base);
                accountProfileClose(&profile);
            }
            u.name = base.nickname[0] ? base.nickname : u.id.substr(0, 8);
            users.push_back(u);
        }
    }
    accountExit();
    return users;
}

ConfigStore& ConfigStore::get() {
    static ConfigStore store;
    return store;
}

bool ConfigStore::load() {
    j_ = json::parse(readFile(kConfigPath), nullptr, false);
    if (j_.is_discarded() || !j_.is_object()) {
        j_ = json::object();
    }
    if (!j_.contains("version")) j_["version"] = 1;
    if (!j_.contains("profiles") || !j_["profiles"].is_array()) j_["profiles"] = json::array();
    if (!j_.contains("network") || !j_["network"].is_object())
        j_["network"] = {{"enabled", true}, {"port", 8460}};
    return true;
}

bool ConfigStore::save() {
    mkdir("sdmc:/config", 0777);
    mkdir("sdmc:/config/nxcontrol", 0777);
    std::string tmp = std::string(kConfigPath) + ".tmp";
    FILE* f = std::fopen(tmp.c_str(), "wb");
    if (!f) return false;
    std::string out = j_.dump(2);
    bool ok = std::fwrite(out.data(), 1, out.size(), f) == out.size();
    std::fclose(f);
    if (!ok) return false;
    remove(kConfigPath);
    return rename(tmp.c_str(), kConfigPath) == 0;
}

json* ConfigStore::findProfile(const std::string& user_id) {
    for (auto& p : j_["profiles"])
        if (p.value("user_id", std::string()) == user_id) return &p;
    return nullptr;
}

json& ConfigStore::ensureProfile(const std::string& user_id, const std::string& name) {
    if (json* p = findProfile(user_id)) {
        (*p)["name"] = name;
        return *p;
    }
    j_["profiles"].push_back({{"user_id", user_id}, {"name", name}, {"mode", "supervised"}, {"rules", json::object()}});
    return j_["profiles"].back();
}

void ConfigStore::removeProfile(const std::string& user_id) {
    auto& arr = j_["profiles"];
    for (auto it = arr.begin(); it != arr.end(); ++it) {
        if (it->value("user_id", std::string()) == user_id) {
            arr.erase(it);
            return;
        }
    }
}

static std::string hashPin(const std::string& pin) {
    std::string salted = "nxcontrol:" + pin;
    u8 hash[SHA256_HASH_SIZE];
    sha256CalculateHash(hash, salted.data(), salted.size());
    char hex[SHA256_HASH_SIZE * 2 + 1];
    for (int i = 0; i < SHA256_HASH_SIZE; i++) std::snprintf(hex + i * 2, 3, "%02x", hash[i]);
    return hex;
}

bool ConfigStore::hasPin() {
    return !j_.value("pin_hash", std::string()).empty();
}

bool ConfigStore::checkPin(const std::string& pin) {
    return hashPin(pin) == j_.value("pin_hash", std::string());
}

void ConfigStore::setPin(const std::string& pin) {
    j_["pin_hash"] = hashPin(pin);
}

json readState() {
    return json::parse(readFile(kStatePath), nullptr, false);
}

std::string formatDuration(long long seconds) {
    if (seconds < 0) return "-";
    char buf[32];
    if (seconds >= 3600) std::snprintf(buf, sizeof(buf), "%lld h %02lld min", seconds / 3600, (seconds % 3600) / 60);
    else std::snprintf(buf, sizeof(buf), "%lld min", seconds / 60);
    return buf;
}

} // namespace nxc
