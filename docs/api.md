# NX Control – Local API v1

The service exposes a REST API on the local network. It is used by the web panel, the Home
Assistant integration and any third-party tool.

- Base URL: `http://<console-ip>:8460/api/v1`
- Discovery: mDNS/DNS-SD `_nxcontrol._tcp.local.` (TXT: `id`, `version`, `api=1`)
- Format: JSON, UTF-8. Times in ISO-8601 local time, durations in **seconds**.
- Network access can be disabled from the app. The API is never exposed outside the LAN by NX Control.

## Authentication

All endpoints except `GET /info` and `POST /pair` require `Authorization: Bearer <token>`.

### Pairing
1. The user opens *NX Control → Network → Pair device*; the console shows a 6-digit code (valid 5 min).
2. The client calls `POST /pair` with the code and receives a long-lived token.
3. Tokens can be revoked from the app.

## Endpoints

### `GET /info` (public)
```json
{ "name": "NX Control", "console_id": "a1b2c3d4", "version": "1.0.0", "api": 1, "console_name": "Switch salón" }
```

### `POST /pair` (public)
```json
// request
{ "code": "482913", "client_name": "Home Assistant" }
// response 200
{ "token": "…", "console_id": "a1b2c3d4" }
```
Errors: `401 invalid_code`, `429 too_many_attempts`.

### `GET /status`
Live state of the console.
```json
{
  "console": { "locked": false, "paused": false, "tamper": false },
  "session": {
    "active": true,
    "profile_id": "0123…cdef",
    "program_id": "0100000000010000",
    "title": "Super Mario Odyssey",
    "started_at": "2026-10-23T17:02:11",
    "focused": true
  },
  "profiles": [
    {
      "id": "0123…cdef",
      "name": "Lucas",
      "mode": "supervised",
      "used_today": 3120,
      "limit_today": 5400,
      "remaining_today": 2280,
      "in_allowed_window": true,
      "state": "playing"
    }
  ],
  "pending_requests": 1
}
```
`state`: `idle` | `playing` | `warning` | `grace` | `exhausted` | `outside_window` | `blocked`.

### Profiles and rules
| Method | Path | Description |
|---|---|---|
| `GET` | `/profiles` | List profiles |
| `GET` | `/profiles/{id}` | Profile with rules |
| `PUT` | `/profiles/{id}` | Update name/mode/rules (commitment rules may return `202 scheduled`) |
| `POST` | `/profiles/{id}/grant` | `{ "seconds": 900, "reason": "…" }` add time for today |
| `POST` | `/profiles/{id}/block` | Block until `{ "until": "…" }` or end of day |
| `POST` | `/profiles/{id}/unblock` | Remove block |

### Usage
`GET /usage?profile={id}&from=YYYY-MM-DD&to=YYYY-MM-DD&group=day|game`
```json
{ "items": [ { "date": "2026-10-22", "program_id": "0100…", "title": "…", "seconds": 2710 } ] }
```

### Time requests
| Method | Path | Description |
|---|---|---|
| `GET` | `/requests?status=pending` | List requests |
| `POST` | `/requests/{id}/approve` | `{ "seconds": 900 }` (optional, defaults to requested) |
| `POST` | `/requests/{id}/deny` | `{ "message": "…" }` |

Request object:
```json
{ "id": "r_17", "profile_id": "…", "seconds": 900, "message": "Terminar el nivel",
  "created_at": "…", "status": "pending|approved|denied|expired" }
```

### Console
| Method | Path | Description |
|---|---|---|
| `POST` | `/console/lock` | Lock all profiles (sends active game to HOME) |
| `POST` | `/console/unlock` | Unlock |
| `POST` | `/console/pause` | Pause NX Control enforcement (tracking continues), `{ "seconds": 3600 }` |

### Events – `GET /events` (Server-Sent Events)
```
event: request_created
data: {"id":"r_17","profile_id":"…","seconds":900,"message":"Terminar el nivel"}
```
| Event | When |
|---|---|
| `session_started` / `session_ended` | A profile starts/stops playing |
| `warning` | A warning threshold is reached (`remaining`) |
| `time_exhausted` | Time is up and the game was suspended |
| `request_created` / `request_resolved` | Time request lifecycle |
| `rules_changed` | Rules updated (from any client) |
| `tamper_detected` | Clock change or play while disabled |

Clients must expect the console to disappear (sleep mode turns Wi-Fi off) and reconnect with backoff.

## Errors
```json
{ "error": "not_found", "message": "Profile not found" }
```
`400 bad_request`, `401 unauthorized`, `403 pin_required`, `404 not_found`, `409 conflict`, `500 internal`.
