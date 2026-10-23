// NX Control - configuration app
#include <borealis.hpp>
#include <cstdlib>
#include "nxc_data.hpp"
#include "nxc_i18n.hpp"
#include "nxc_ui.hpp"

int main(int argc, char* argv[]) {
    nxc::initLanguage();

    brls::Platform::APP_LOCALE_DEFAULT = brls::LOCALE_AUTO;
    if (!brls::Application::init()) {
        brls::Logger::error("Unable to init Borealis application");
        return EXIT_FAILURE;
    }
    brls::Application::createWindow("NX Control");
    brls::Application::getPlatform()->setThemeVariant(brls::ThemeVariant::DARK);
    brls::Application::setGlobalQuit(true);

    nxc::ConfigStore::get().load();
    bool firstRun = !nxc::ConfigStore::get().hasPin();

    // Without a PIN there is nothing to protect yet.
    nxc::ui::setUnlocked(firstRun);
    nxc::ui::showMain();

    if (firstRun) {
        nxc::ui::showWelcome();
    } else {
        brls::sync([] { nxc::ui::askPin(nullptr); });
    }

    while (brls::Application::mainLoop())
        ;
    return EXIT_SUCCESS;
}
