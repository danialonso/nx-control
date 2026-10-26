// NX Control - quick panel (Tesla overlay)
#define TESLA_INIT_IMPL
#include <tesla.hpp>
#include <nlohmann/json.hpp>
#include <cstdio>
#include <cstdlib>
#include <string>

using nlohmann::json;

namespace {

constexpr const char *kStatePath = "sdmc:/config/nxcontrol/state.json";

std::string formatDuration(long long seconds) {
    if (seconds < 0) return "Unlimited";
    char buf[32];
    if (seconds >= 3600) std::snprintf(buf, sizeof(buf), "%lldh %02lldm", seconds / 3600, (seconds % 3600) / 60);
    else                 std::snprintf(buf, sizeof(buf), "%lldm %02llds", seconds / 60, seconds % 60);
    return buf;
}

json readState() {
    FILE *f = std::fopen(kStatePath, "rb");
    if (!f) return json();
    std::string text;
    char buf[1024]; size_t n;
    while ((n = std::fread(buf, 1, sizeof(buf), f)) > 0) text.append(buf, n);
    std::fclose(f);
    return json::parse(text, nullptr, false);
}

class MainGui : public tsl::Gui {
public:
    tsl::elm::Element *createUI() override {
        auto frame = new tsl::elm::OverlayFrame("NX Control", NXC_VERSION);
        auto list  = new tsl::elm::List();

        list->addItem(new tsl::elm::CategoryHeader("Today"));
        profile_   = new tsl::elm::ListItem("Profile", "-");
        remaining_ = new tsl::elm::ListItem("Time remaining", "-");
        used_      = new tsl::elm::ListItem("Played today", "-");
        status_    = new tsl::elm::ListItem("Status", "-");
        list->addItem(profile_);
        list->addItem(remaining_);
        list->addItem(used_);
        list->addItem(status_);

        list->addItem(new tsl::elm::CategoryHeader("Need more time?"));
        request_ = new tsl::elm::ListItem("Request", "-");
        list->addItem(request_);
        for (int minutes : {15, 30, 60}) {
            auto item = new tsl::elm::ListItem("Ask for " + std::to_string(minutes) + " more minutes");
            item->setClickListener([this, minutes](u64 keys) {
                if (!(keys & HidNpadButton_A)) return false;
                sendRequest(minutes);
                return true;
            });
            list->addItem(item);
        }

        frame->setContent(list);
        refresh();
        return frame;
    }

    void update() override {
        if (++frames_ % 60 == 0) refresh();
    }

private:
    // The service picks up files from the inbox folder within a second.
    void sendRequest(int minutes) {
        if (profile_id_.empty()) {
            request_->setValue("No game running");
            return;
        }
        json cmd = {{"type", "request"}, {"profile_id", profile_id_}, {"seconds", minutes * 60}};
        char base[96];
        std::snprintf(base, sizeof(base), "sdmc:/config/nxcontrol/inbox/ovl_%lu", armGetSystemTick());
        std::string tmp = std::string(base) + ".tmp", final_path = std::string(base) + ".json";
        if (FILE *f = std::fopen(tmp.c_str(), "wb")) {
            std::string out = cmd.dump();
            std::fwrite(out.data(), 1, out.size(), f);
            std::fclose(f);
            std::rename(tmp.c_str(), final_path.c_str());
            request_->setValue("Sent, waiting...");
        } else {
            request_->setValue("Could not send");
        }
    }

    void refresh() {
        json s = readState();
        if (s.is_discarded() || !s.is_object()) {
            status_->setValue("Service not running");
            return;
        }
        const json &session = s["session"];
        std::string pid = session.value("profile_id", std::string());
        profile_id_ = pid;
        std::string req = "-";
        if (s.contains("requests") && s["requests"].is_array())
            for (const auto &r : s["requests"])
                if (r.value("profile_id", std::string()) == pid) {
                    std::string st = r.value("status", std::string());
                    long long mins = r.value("seconds", 0LL) / 60;
                    if (st == "pending") req = "Waiting (" + std::to_string(mins) + " min)";
                    else if (st == "approved") req = "Approved (+" + std::to_string(mins) + " min)";
                    else if (st == "denied") req = "Denied";
                }
        request_->setValue(req);
        status_->setValue(session.value("state", std::string("idle")));

        for (const auto &p : s["profiles"]) {
            if (p.value("id", std::string()) != pid) continue;
            profile_->setValue(p.value("name", std::string("-")));
            remaining_->setValue(formatDuration(p.value("remaining_today", -1LL)));
            used_->setValue(formatDuration(p.value("used_today", 0LL)));
            return;
        }
        profile_->setValue(pid.empty() ? "No game running" : "Not configured");
        remaining_->setValue("-");
        used_->setValue("-");
    }

    tsl::elm::ListItem *profile_ = nullptr, *remaining_ = nullptr, *used_ = nullptr, *status_ = nullptr;
    tsl::elm::ListItem *request_ = nullptr;
    std::string profile_id_;
    u32 frames_ = 0;
};

class NxControlOverlay : public tsl::Overlay {
public:
    void initServices() override { fsdevMountSdmc(); }
    void exitServices() override {}
    std::unique_ptr<tsl::Gui> loadInitialGui() override { return initially<MainGui>(); }
};

} // namespace

int main(int argc, char **argv) {
    return tsl::loop<NxControlOverlay>(argc, argv);
}
