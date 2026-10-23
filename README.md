<div align="center">

# NX Control

**Conscious play time, healthy digital habits and usage insights for Nintendo Switch (Atmosphère CFW).**

Local-first · Private · No cloud · No accounts · Open source

</div>

---

NX Control is a native-feeling time and habit management system for Nintendo Switch consoles
running Atmosphère. It is designed for everyone:

- **Families** – daily limits, allowed hours, time requests and approvals.
- **Teenagers** – self-managed goals and limits.
- **Adults** – habit tracking, commitment rules and personal discipline.
- **Data lovers** – detailed, private usage analytics.
- **Smart homes** – optional, first-class Home Assistant integration.

It is **not** just a parental control tool: every profile can be *Supervised*, *Self-managed* or
*Analytics only*.

## Principles

| | |
|---|---|
| **Local first** | Everything works without Internet. |
| **No cloud** | No servers, no SaaS, no subscriptions, no accounts. |
| **Your data** | NX Control collects nothing and sends no telemetry. |
| **Optional integrations** | Home Assistant is a bonus, never a requirement. |
| **One product** | One download, one install, one experience. |

## Features

- Per-profile rules linked to the console users
  - Daily / weekly time budgets, per-day overrides and special days
  - Allowed time windows
  - Per-game and per-category limits
  - Session length limits with mandatory breaks
- Warnings at 15, 5 and 1 minutes with a configurable grace period
- **No lost progress**: when time is up, the game is suspended (sent to HOME), never killed
- Extra-time requests, approved with PIN on the console, from the web panel or from Home Assistant
- Commitment mode: relaxing a rule takes 24 h, tightening it is immediate
- Statistics from day one (imports the console's own play history)
- Clock-tamper protection and detection of play while NX Control was disabled
- NX Control app, Tesla overlay and local web panel
- Home Assistant integration through HACS with auto-discovery
- English and Spanish

## Installation (console)

1. Download `NX-Control-x.y.z.zip` from [Releases](https://github.com/danialonso/nx-control/releases).
2. Extract it to the **root of your SD card** (merge folders).
3. Reboot the console.
4. Open **NX Control** from the Homebrew Menu and follow the setup wizard (PIN + profiles).

Requirements: Atmosphère, and [Ultrahand / Tesla overlay loader](https://github.com/ppkantorski/Ultrahand-Overlay) for the quick panel.

## Installation (Home Assistant, optional)

1. In HACS, add `https://github.com/danialonso/nx-control` as a **custom repository** (type: *Integration*).
2. Install **NX Control** and restart Home Assistant.
3. Your console is discovered automatically. Confirm it and enter the pairing code shown on the console.

## Repository layout

| Folder | Content |
|---|---|
| `sysmodule/` | Background service (rules engine, tracking, enforcement, local API) |
| `app/` | NX Control configuration app |
| `overlay/` | Tesla quick panel |
| `custom_components/nx_control/` | Home Assistant integration (HACS) |
| `docs/` | Architecture, data model and local API specification |
| `dist-template/` | Default files shipped on the SD card |

## Building

The easiest way is to push a tag: GitHub Actions builds everything and attaches the SD-ready zip to the release.

Locally (devkitPro with `switch-dev` installed):

```sh
./scripts/fetch-deps.sh
make dist
```

## Status

🚧 Early development. See [docs/architecture.md](docs/architecture.md).

## License

GPL-3.0. See [LICENSE](LICENSE).

NX Control is not affiliated with or endorsed by Nintendo.
