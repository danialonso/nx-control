#pragma once
#include <switch.h>
#include <string>

namespace nxc {

struct Foreground {
    bool running = false;     // an application (game) process exists
    bool focused = false;     // the application is on screen (not suspended in HOME)
    u64  program_id = 0;
    std::string user_id;      // user that launched the application
};

// Detects which game is running, with which user, and whether it is on screen.
class Tracker {
public:
    Result init();
    void exit();
    Foreground poll();

private:
    void readFocusEvents();

    bool pdm_ok_ = false;
    s32  next_event_ = -1;       // next pdm play event index to read
    u64  current_pid_ = 0;       // process id of the tracked application
    u64  current_program_ = 0;
    bool focused_ = false;
    std::string user_;
    u32 now_check_user_ = 0;
};

} // namespace nxc
