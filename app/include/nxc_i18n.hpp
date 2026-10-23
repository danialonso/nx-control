#pragma once
#include <string>

namespace nxc {
// Tiny built-in translation table (English / Spanish), chosen from the console language.
void initLanguage();
const std::string& tr(const char* key);
bool isSpanish();
}
