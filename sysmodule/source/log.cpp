#include "log.hpp"
#include "common.hpp"
#include <cstdarg>
#include <cstdio>
#include <sys/stat.h>

namespace nxc::log {

static void rotateIfNeeded(const char *path) {
    struct stat st;
    if (stat(path, &st) == 0 && st.st_size > 256 * 1024) {
        std::string old = std::string(path) + ".1";
        remove(old.c_str());
        rename(path, old.c_str());
    }
}

static void write(const char *path, const char *prefix, const char *fmt, va_list args) {
    rotateIfNeeded(path);
    FILE *f = std::fopen(path, "a");
    if (!f) return;
    LocalNow now = localNow();
    std::fprintf(f, "%s %s ", now.valid ? now.iso.c_str() : "----", prefix);
    std::vfprintf(f, fmt, args);
    std::fputc('\n', f);
    std::fclose(f);
}

void debug(const char *fmt, ...) {
    va_list a; va_start(a, fmt);
    write(kDebugLog, "[nxc]", fmt, a);
    va_end(a);
}

void event(const char *type, const char *fmt, ...) {
    va_list a; va_start(a, fmt);
    write(kEventsLog, type, fmt, a);
    va_end(a);
}

} // namespace nxc::log
