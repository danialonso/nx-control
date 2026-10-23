#include "enforcer.hpp"
#include "log.hpp"

namespace nxc {

alignas(0x1000) static u8 g_hdls_workmem[0x1000];

Result Enforcer::init() {
    Result rc = hiddbgInitialize();
    ok_ = R_SUCCEEDED(rc);
    if (!ok_) log::debug("hid:dbg init failed 0x%x", rc);
    Result rc2 = pmshellInitialize();
    if (R_FAILED(rc2)) log::debug("pm:shell init failed 0x%x", rc2);
    return rc;
}

void Enforcer::exit() {
    if (ok_) hiddbgExit();
    pmshellExit();
    ok_ = false;
}

Result Enforcer::sendToHome() {
    if (!ok_) return MAKERESULT(Module_Libnx, LibnxError_NotInitialized);

    HiddbgHdlsSessionId session = {};
    Result rc = hiddbgAttachHdlsWorkBuffer(&session, g_hdls_workmem, sizeof(g_hdls_workmem));
    if (R_FAILED(rc)) { log::debug("AttachHdlsWorkBuffer 0x%x", rc); return rc; }

    HiddbgHdlsDeviceInfo info = {};
    info.deviceType        = HidDeviceType_FullKey15;   // Pro Controller
    info.npadInterfaceType = HidNpadInterfaceType_USB;
    info.singleColorBody    = RGBA8_MAXALPHA(0x20, 0x20, 0x20);
    info.singleColorButtons = RGBA8_MAXALPHA(0xFF, 0xFF, 0xFF);
    info.colorLeftGrip      = RGBA8_MAXALPHA(0x20, 0x20, 0x20);
    info.colorRightGrip     = RGBA8_MAXALPHA(0x20, 0x20, 0x20);

    HiddbgHdlsHandle handle = {};
    rc = hiddbgAttachHdlsVirtualDevice(&handle, &info);
    if (R_SUCCEEDED(rc)) {
        HiddbgHdlsState state = {};
        state.battery_level = 4;
        svcSleepThread(200'000'000ULL);              // let the system register the device
        state.buttons = HiddbgNpadButton_Home;
        hiddbgSetHdlsState(handle, &state);
        svcSleepThread(120'000'000ULL);
        state.buttons = 0;
        hiddbgSetHdlsState(handle, &state);
        svcSleepThread(80'000'000ULL);
        hiddbgDetachHdlsVirtualDevice(handle);
    } else {
        log::debug("AttachHdlsVirtualDevice 0x%x", rc);
    }
    hiddbgReleaseHdlsWorkBuffer(session);
    return rc;
}

Result Enforcer::closeApplication() {
    u64 pid = 0;
    Result rc = pmdmntGetApplicationProcessId(&pid);
    if (R_FAILED(rc) || pid == 0) return rc;
    rc = pmshellTerminateProcess(pid);
    if (R_FAILED(rc)) log::debug("TerminateProcess 0x%x", rc);
    return rc;
}

} // namespace nxc
