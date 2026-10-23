// NX Control - quick panel (Tesla overlay)
#define TESLA_INIT_IMPL
#include <tesla.hpp>
#include <nlohmann/json.hpp>
#include <cstdio>
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
        for (int minutes : {15, 30}) {
            auto item = new tsl::elm::ListItem("Request " + std::to_string(minutes) + " minutes");
            item->setClickListener([](u64 keys) {
                // TODO: send request to the service (IPC) and show PIN approval
                return (keys & HidNpadButton_A) != 0;
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
    void refresh() {
        json s = readState();
        if (s.is_discarded() || !s.is_object()) {
            status_->setValue("Service not running");
            return;
        }
        const json &session = s["session"];
        std::string pid = session.value("profile_id", std::string());
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
