#!/usr/bin/env bash
# Builds the NX Control app (Borealis UI) as nxcontrol.nro.
# The app sources in app/ are placed inside a copy of the Borealis tree,
# which provides the Switch build setup (CMake + deko3d).
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="${1:-0.0.0-dev}"
ROOT="$(pwd)"
B="$ROOT/build/app-borealis"

rm -rf "$B"
mkdir -p "$ROOT/build"
cp -r "$ROOT/external/borealis" "$B"

# Replace the Borealis demo with the NX Control app
rm -rf "$B/demo"
mkdir -p "$B/demo/include/nlohmann"
cp "$ROOT"/app/source/*.cpp "$B/demo/"
cp "$ROOT"/app/include/*.hpp "$B/demo/include/"
cp "$ROOT/external/json/nlohmann/json.hpp" "$B/demo/include/nlohmann/"
cp "$ROOT/app/icon.jpg" "$B/resources/img/demo_icon.jpg"

# Project name, author, version and title shown in the Homebrew Menu
sed -i \
  -e 's/project(borealis_demo)/project(nxcontrol)/' \
  -e 's/set(PROJECT_AUTHOR "borealis")/set(PROJECT_AUTHOR "NX Control contributors")/' \
  -e "s/--create \"\${PROJECT_NAME}\"/--create \"NX Control\"/" \
  -e "s/\"\${VERSION_MAJOR}.\${VERSION_MINOR}.\${VERSION_ALTER}\" \${PROJECT_NAME}.nacp/\"$VERSION\" \${PROJECT_NAME}.nacp/" \
  "$B/CMakeLists.txt"
printf '#pragma once\n#define NXC_VERSION "%s"\n' "$VERSION" > "$B/demo/include/nxc_version.hpp"

cmake -S "$B" -B "$B/build" -DCMAKE_BUILD_TYPE=Release -DPLATFORM_SWITCH=ON -DUSE_DEKO3D=ON
make -C "$B/build" nxcontrol.nro -j"$(nproc)"
cp "$B/build/nxcontrol.nro" "$ROOT/app/nxcontrol.nro"
echo "App built: app/nxcontrol.nro"
