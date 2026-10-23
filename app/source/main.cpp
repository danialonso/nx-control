// NX Control - app (temporary console UI; the Borealis UI replaces it)
#include <switch.h>
#include <nlohmann/json.hpp>
#include <cstdio>
#include <string>

using nlohmann::json;

static json readState() {
    FILE *f = std::fopen("sdmc:/config/nxcontrol/state.json", "rb");
    if (!f) return json();
    std::string text;
    char buf[1024]; size_t n;
    while ((n = std::fread(buf, 1, sizeof(buf), f)) > 0) text.append(buf, n);
    std::fclose(f);
    return json::parse(text, nullptr, false);
}

static void printUsers() {
    if (R_FAILED(accountInitialize(AccountServiceType_Application))) return;
    AccountUid uids[ACC_USER_LIST_SIZE];
    s32 count = 0;
    if (R_SUCCEEDED(accountListAllUsers(uids, ACC_USER_LIST_SIZE, &count))) {
        std::printf("\nConsole users (use these IDs in config.json):\n");
        for (s32 i = 0; i < count; i++) {
            AccountProfile profile;
            AccountProfileBase base = {};
            if (R_SUCCEEDED(accountGetProfile(&profile, uids[i]))) {
                accountProfileGet(&profile, nullptr, &base);
                accountProfileClose(&profile);
            }
            std::printf("  %-20s %016lx%016lx\n", base.nickname, uids[i].uid[0], uids[i].uid[1]);
        }
    }
    accountExit();
}

int main(int, char **) {
    consoleInit(nullptr);
    padConfigureInput(1, HidNpadStyleSet_NpadStandard);
    PadState pad;
    padInitializeDefault(&pad);

    std::printf("NX Control %s\n\n", NXC_VERSION);
    json s = readState();
    if (s.is_discarded() || !s.is_object()) {
        std::printf("The NX Control service is not running.\nReboot the console after installing.\n");
    } else {
        std::printf("Service running (%s)\n\nProfiles:\n", s.value("version", std::string("?")).c_str());
        for (const auto &p : s["profiles"])
            std::printf("  %-16s used %4llds  remaining %6llds\n",
                        p.value("name", std::string("-")).c_str(),
                        p.value("used_today", 0LL), p.value("remaining_today", -1LL));
    }
    printUsers();
    std::printf("\nPress + to exit.\n");

    while (appletMainLoop()) {
        padUpdate(&pad);
        if (padGetButtonsDown(&pad) & HidNpadButton_Plus) break;
        consoleUpdate(nullptr);
    }
    consoleExit(nullptr);
    return 0;
}
