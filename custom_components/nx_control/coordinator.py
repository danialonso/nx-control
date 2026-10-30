"""Data coordinator for NX Control."""
from __future__ import annotations

import calendar
from datetime import date, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import NXControlAuthError, NXControlClient, NXControlError
from .const import (
    DOMAIN,
    EVENT_SESSION_ENDED,
    EVENT_SESSION_STARTED,
    EVENT_TIME_REQUEST,
    PLAYING_STATES,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

USAGE_INTERVAL = timedelta(minutes=5)
REPORT_DAYS = 7
NOT_GAMES = {"nx-hbmenu", "hbmenu", "Homebrew Menu", "NX Control"}


class NXControlCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the console, keeps the last known data when it is off, and builds play reports."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: NXControlClient) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL, config_entry=entry)
        self.client = client
        self._known_requests: set[str] = set()
        from .notify import NXControlNotifier
        self.notifier = NXControlNotifier(hass, entry, self)
        self._playing: dict[str, bool] | None = None  # None until the first update
        self._store: Store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self._cache: dict[str, Any] | None = None
        self._usage: list[dict[str, Any]] = []
        self._usage_at = None
        self._saved_at = None

    @property
    def online(self) -> bool:
        return bool((self.data or {}).get("online"))

    async def async_load_cache(self) -> None:
        stored = await self._store.async_load()
        if isinstance(stored, dict):
            self._cache = stored.get("status")
            self._usage = stored.get("usage") or []

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            status = await self.client.status()
            requests = await self.client.pending_requests()
        except NXControlAuthError as err:
            raise ConfigEntryAuthFailed from err
        except NXControlError as err:
            # Console off or asleep: keep showing the last known data (reports stay visible)
            if self._cache:
                return self._offline_data()
            raise UpdateFailed(str(err)) from err

        current = set()
        new_requests = []
        for req in requests:
            req_id = str(req.get("id"))
            current.add(req_id)
            if req_id not in self._known_requests:
                new_requests.append(req)
                self.hass.bus.async_fire(EVENT_TIME_REQUEST, {
                    "request_id": req_id,
                    "profile_id": req.get("profile_id"),
                    "profile_name": self.profile_name(req.get("profile_id"), status),
                    "minutes": int(req.get("seconds", 0)) // 60,
                    "message": req.get("message", ""),
                    "console_id": self.config_entry.unique_id,
                })
        # Phone notifications: new requests, and requests answered since the last update
        all_requests = {str(r.get("id")): r for r in status.get("requests") or [] if isinstance(r, dict)}
        for req in new_requests:
            await self.notifier.async_new_request(req, self.profile_name(req.get("profile_id"), status))
        for req_id in self._known_requests - current:
            await self.notifier.async_resolved(all_requests.get(req_id), req_id)
        self._known_requests = current
        self._fire_session_events(status)
        status["requests"] = requests

        now = dt_util.utcnow()
        if self._usage_at is None or now - self._usage_at >= USAGE_INTERVAL:
            try:
                start = (dt_util.now().date() - timedelta(days=REPORT_DAYS - 1)).isoformat()
                self._usage = await self.client.usage(start)
                self._usage_at = now
                # Keep game icons and avatars cached, so they still show when the console is off
                from .images import async_prefetch
                self.config_entry.async_create_background_task(
                    self.hass, async_prefetch(self.hass, self, status, self._usage), "nx_control_images")
            except NXControlError as err:
                _LOGGER.debug("Could not read usage: %s", err)

        status["online"] = True
        status["last_seen"] = now.isoformat()
        status["usage"] = self._usage
        self._cache = {k: v for k, v in status.items() if k not in ("usage", "online")}
        if self._saved_at is None or now - self._saved_at >= USAGE_INTERVAL:
            self._saved_at = now
            await self._store.async_save({"status": self._cache, "usage": self._usage})
        return status

    def _offline_data(self) -> dict[str, Any]:
        """Last known data, with nobody playing."""
        data = dict(self._cache or {})
        data["profiles"] = [{**p, "state": "offline"} for p in data.get("profiles", [])]
        data["session"] = {"active": False}
        data["requests"] = []
        data["online"] = False
        data["usage"] = self._usage
        self._start_new_day(data)
        if self._playing:
            self._fire_session_events(data)   # "stopped playing" when the console goes off
        return data

    @staticmethod
    def _start_new_day(data: dict[str, Any]) -> None:
        """Console off since an earlier day: show today as the console would when it turns on.

        Played time and extra time go back to zero, today's limit and allowed hours come from the
        weekly schedule the console sent, "blocked for today" and "no limits until 0:00" end at
        midnight, and the console lock stays. The console's own data replaces this when it is back.
        """
        snapshot_day = str(data.get("updated_at") or "")[:10]
        now = dt_util.now()
        if len(snapshot_day) != 10 or snapshot_day >= now.date().isoformat():
            return
        # The console counts in local wall-clock seconds (its clock as if it were UTC)
        wall = calendar.timegm(now.replace(tzinfo=None).timetuple())
        weekday = now.weekday()                     # 0 = Monday, like the console
        minute = now.hour * 60 + now.minute

        console = dict(data.get("console") or {})
        console["paused"] = False
        console["paused_until"] = 0
        data["console"] = console
        locked = bool(console.get("locked"))

        profiles = []
        for p in data.get("profiles", []):
            q = {k: v for k, v in p.items() if not k.startswith("game_")}
            q["used_today"] = 0
            schedule = p.get("schedule")
            if isinstance(schedule, dict):
                days = schedule.get("daily_minutes") or []
                minutes = days[weekday] if len(days) == 7 and isinstance(days[weekday], int) else -1
                limit = minutes * 60 if minutes >= 0 else -1
                remaining = limit
                in_window, window_ends = True, -1
                windows = [w for w in schedule.get("windows") or [] if isinstance(w, dict)]
                if windows:
                    in_window = False
                    for w in windows:
                        if not int(w.get("days", 0x7F)) & (1 << weekday):
                            continue
                        start, end = int(w.get("from", 0)), int(w.get("to", 24 * 60))
                        if start <= minute < end:
                            in_window = True
                            ends = (end - minute) * 60 - now.second
                            window_ends = max(window_ends, ends)
                if window_ends >= 0 and (remaining < 0 or window_ends < remaining):
                    remaining = window_ends
                q["limit_today"], q["remaining_today"], q["in_allowed_window"] = limit, remaining, in_window
            elif p.get("limit_today") not in (None, -1):
                # Console without the weekly schedule (older version): today's limit is not known
                q["limit_today"] = q["remaining_today"] = None
            profile_blocked = int(p.get("blocked_until") or 0) > wall
            q["profile_blocked"] = profile_blocked
            q["blocked"] = locked or profile_blocked
            profiles.append(q)
        data["profiles"] = profiles
        data["new_day"] = True

    def _fire_session_events(self, status: dict[str, Any]) -> None:
        """Fire an event when a profile starts or stops playing."""
        session = status.get("session", {})
        playing = {
            p.get("id"): p.get("state") in PLAYING_STATES for p in status.get("profiles", [])
        }
        if self._playing is not None:  # no events for the state found at startup
            for profile_id, is_playing in playing.items():
                if is_playing == self._playing.get(profile_id, False):
                    continue
                data = {
                    "profile_id": profile_id,
                    "profile_name": self.profile_name(profile_id, status),
                    "console_id": self.config_entry.unique_id,
                }
                if is_playing:
                    data["game"] = session.get("title") or session.get("program_id")
                    self.hass.bus.async_fire(EVENT_SESSION_STARTED, data)
                else:
                    self.hass.bus.async_fire(EVENT_SESSION_ENDED, data)
        self._playing = playing

    def report(self, profile_id: str) -> dict[str, Any]:
        """Games and daily totals of the last days for one profile."""
        today = dt_util.now().date()
        days = [(today - timedelta(days=i)).isoformat() for i in range(REPORT_DAYS - 1, -1, -1)]
        daily = {d: 0 for d in days}
        today_games: dict[str, dict[str, Any]] = {}
        week_games: dict[str, dict[str, Any]] = {}
        for item in (self.data or {}).get("usage", []):
            if item.get("profile_id") != profile_id or item.get("date") not in daily:
                continue
            if item.get("title") in NOT_GAMES:
                continue
            secs = int(item.get("seconds") or 0)
            pid = item.get("program_id")
            daily[item["date"]] += secs
            for bucket, include in ((week_games, True), (today_games, item["date"] == days[-1])):
                if not include:
                    continue
                g = bucket.setdefault(pid, {"program_id": pid, "title": item.get("title") or pid, "seconds": 0})
                g["seconds"] += secs
        top = lambda d: sorted(d.values(), key=lambda g: g["seconds"], reverse=True)
        return {
            "daily": [{"date": d, "seconds": daily[d]} for d in days],
            "week_seconds": sum(daily.values()),
            "games_today": top(today_games)[:6],
            "games_week": top(week_games)[:6],
        }

    @staticmethod
    def profile_name(profile_id: str | None, status: dict[str, Any]) -> str:
        for p in status.get("profiles", []):
            if p.get("id") == profile_id:
                return p.get("name", "")
        return ""
