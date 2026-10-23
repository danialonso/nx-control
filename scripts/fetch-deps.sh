#!/usr/bin/env bash
# Downloads third-party build dependencies into ./external
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p external

# nlohmann/json (single header)
if [ ! -f external/json/nlohmann/json.hpp ]; then
  mkdir -p external/json/nlohmann
  wget -q -O external/json/nlohmann/json.hpp \
    https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp
fi

# libtesla (overlay framework)
if [ ! -d external/libtesla ]; then
  git clone --depth 1 https://github.com/WerWolv/libtesla.git external/libtesla
fi

echo "Dependencies ready."
