#pragma once
#include <borealis.hpp>

namespace nxc::ui {
// Pushes the main NX Control screen (tabs: Today, Profiles, Settings).
void showMain();
// First launch: asks the user to create a PIN, then shows the main screen.
void showWelcome();
// Asks for the PIN; calls onSuccess() if correct.
void askPin(std::function<void()> onSuccess);
bool isUnlocked();
void setUnlocked(bool unlocked);
}
