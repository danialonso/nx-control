"""Data coordinator for NX Control."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NXControlAuthError, NXControlClient, NXControlError
from .const import DOMAIN, EVENT_TIME_REQUEST, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class NXControlCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the console and fires events for new time requests."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: NXControlClient) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL, config_entry=entry)
        self.client = client
        self._known_requests: set[str] = set()

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            status = await self.client.status()
            requests = await self.client.pending_requests()
        except NXControlAuthError as err:
            raise ConfigEntryAuthFailed from err
        except NXControlError as err:
            # Console asleep or offline: entities become unavailable.
            raise UpdateFailed(str(err)) from err

        current = set()
        for req in requests:
            req_id = str(req.get("id"))
            current.add(req_id)
            if req_id not in self._known_requests:
                self.hass.bus.async_fire(EVENT_TIME_REQUEST, {
                    "request_id": req_id,
                    "profile_id": req.get("profile_id"),
                    "profile_name": self.profile_name(req.get("profile_id"), status),
                    "minutes": int(req.get("seconds", 0)) // 60,
                    "message": req.get("message", ""),
                    "console_id": self.config_entry.unique_id,
                })
        self._known_requests = current
        status["requests"] = requests
        return status

    @staticmethod
    def profile_name(profile_id: str | None, status: dict[str, Any]) -> str:
        for p in status.get("profiles", []):
            if p.get("id") == profile_id:
                return p.get("name", "")
        return ""
