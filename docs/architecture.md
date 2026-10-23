# NX Control – Architecture

NX Control is **one product**. Internally it is made of several components that are always
installed, versioned and released together.

```
┌──────────────────────────── Nintendo Switch (Atmosphère) ────────────────────────────┐
│                                                                                       │
│  ┌──────────────┐   ┌──────────────┐        ┌──────────────────────────────────────┐ │
│  │ NX Control   │   │ Quick panel  │        │ NX Control service (sysmodule)        │ │
│  │ app (.nro)   │   │ overlay(.ovl)│◄──────►│  • Tracker (foreground app + user)    │ │
│  └──────┬───────┘   └──────┬───────┘  IPC   │  • Rules engine                        │ │
│         └──────────────────┴──────────────► │  • Enforcer (warnings, HOME, lock)     │ │
│                                             │  • Usage store (SD card)               │ │
│                                             │  • Local API (HTTP + SSE) + mDNS       │ │
│                                             └──────────────────┬───────────────────┘ │
└────────────────────────────────────────────────────────────────┼─────────────────────┘
                                                                 │ LAN only
                               ┌─────────────────────────────────┼──────────────────┐
                               │                                 │                  │
                        ┌──────▼──────┐                 ┌────────▼────────┐         │
                        │ Web panel   │                 │ Home Assistant  │         │
                        │ (served by  │                 │ integration     │         │
                        │  console)   │                 │ (HACS)          │         │
                        └─────────────┘                 └─────────────────┘         │
```

## Components

| Component | Responsibility |
|---|---|
| **Service** (`sysmodule/`) | Always running from boot (boot2). Single source of truth: tracking, rules, enforcement, storage, API. |
| **App** (`app/`) | Setup wizard, profiles, rules, statistics, PIN, pairing codes. |
| **Overlay** (`overlay/`) | Remaining time, time requests, PIN approval, works on top of games and HOME. |
| **Web panel** (`web/`) | Mobile-friendly management from the LAN, served by the service. |
| **HA integration** (`custom_components/nx_control/`) | Entities, actions, events and actionable notifications. |

All clients (app, overlay, web, Home Assistant) talk to the service. **No client keeps its own
rules or counters.**

## Key technical decisions

### Foreground detection
- Running application: `pm:dmnt` (`GetApplicationProcessId`) + `pm:info` (`GetProgramId`).
- Active user: `acc` (`GetLastOpenedUser`).
- Focus (in game vs. HOME menu): system play log `pdm:qry` applet events
  (`InFocus` / `OutOfFocus`). Only focused time is counted. *To validate on hardware: event latency.*

### Time source and tamper resistance
- Durations are measured with the monotonic system tick, never with the wall clock.
- The wall clock is only used to know *which day* and *which time window* it is.
- Wall clock jumps are detected by comparing tick deltas with wall-clock deltas and logged as tamper events.
- On boot, the console's own play log (`pdm`) is compared with NX Control's records to detect play while NX Control was disabled.

### Enforcement: suspend, never kill
1. Warnings at the configured thresholds (default 15, 5, 1 min).
2. Grace period (default 60 s, configurable, useful for online matches).
3. The game is **sent to HOME** (suspended) by emitting a HOME press through a virtual HDLS controller (`hid:dbg`).
4. If the game regains focus without time, it is sent back to HOME immediately.
5. New games cannot be started without time (they are sent back to HOME on focus).
6. Optional: close the suspended game after N minutes (off by default).

> ⚠️ Pressing HOME while the HOME menu is focused *resumes* the game, so the enforcer only acts when the game is known to be focused.

### Native warnings (research)
The `pctl` service exposes Play Timer commands. We will evaluate whether they can be used *only* to
trigger the native "time is almost up" notification. Rules are never stored in Nintendo's parental
controls (console-wide, cloud-managed, may conflict with an existing pairing).

### Storage (SD card)
```
/config/nxcontrol/
├── config.json          # profiles, rules, settings (written by the service only)
├── state.json           # live state snapshot (read by app/overlay)
├── usage/
│   ├── today.json       # counters for the current day
│   └── history.csv      # one line per day/user/game
├── events.log           # append-only audit log (warnings, kicks, requests, tamper)
└── log.txt              # diagnostics
```

### Memory budget
Sysmodules run in a small memory pool. Target: **< 1 MB heap**. No database engine; append-only
files + daily aggregates. The HTTP server handles a few concurrent clients.

### IPC between console components
The service registers the `nxctl` service. Until it is implemented, the app and overlay read
`state.json` (read-only) and write requests to `/config/nxcontrol/inbox/`.

## Data model

```
Profile
 ├── user_id            (console account UID, 32 hex chars)
 ├── name
 ├── mode               supervised | self | analytics
 └── rules
      ├── daily_minutes            { mon..sun: minutes | null (unlimited) }
      ├── weekly_minutes           minutes | null
      ├── allowed_windows          [ { days:[...], from:"HH:MM", to:"HH:MM" } ]
      ├── special_days             [ { date:"YYYY-MM-DD", daily_minutes, windows } ]
      ├── game_limits              [ { program_id, daily_minutes } ]
      ├── session                  { max_minutes, break_minutes }
      ├── warnings_minutes         [15, 5, 1]
      ├── grace_seconds            60
      ├── close_after_minutes      0 (disabled)
      └── commitment_hours         0 (supervised) / 24 (self, optional)
```
