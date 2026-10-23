#pragma once

namespace nxc::log {
// Diagnostics (log.txt). Kept small: rotated when larger than 256 KB.
void debug(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
// Audit trail (events.log): warnings, kicks, requests, tamper...
void event(const char *type, const char *fmt, ...) __attribute__((format(printf, 2, 3)));
}
