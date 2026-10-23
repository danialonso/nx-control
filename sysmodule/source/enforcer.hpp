#pragma once
#include <switch.h>

namespace nxc {

// Suspends the running game by sending it to the HOME menu (no progress is lost).
class Enforcer {
public:
    Result init();
    void exit();
    // Emits a HOME button press through a temporary virtual controller.
    Result sendToHome();
    // Optional hard stop (only used when "close_after_minutes" is configured).
    Result closeApplication();

private:
    bool ok_ = false;
};

} // namespace nxc
