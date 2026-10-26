# NX Control quick panel (Tesla overlay)

This is the only part of NX Control whose source code is public. It is free software under the
GNU General Public License (see `LICENSE` in this folder), because it is built on
[libtesla](https://github.com/WerWolv/libtesla).

The quick panel shows the profile playing, time left and time played, and lets the player ask for
more time. It talks to the NX Control service through JSON files in `/config/nxcontrol/`.

## Building

Requires devkitPro (`switch-dev`), [libtesla](https://github.com/WerWolv/libtesla) in
`../external/libtesla` and [nlohmann/json](https://github.com/nlohmann/json) in `../external/json`.

```sh
make APP_VERSION=1.0.0
```

The result is `nxcontrol.ovl`, installed to `/switch/.overlays/` on the SD card.
