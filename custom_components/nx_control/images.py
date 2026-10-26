"""Game icons and user avatars, cached on the Home Assistant disk.

They are fetched from the console while it is on and kept, so reports and the card still
show them when the console is off.
"""
from __future__ import annotations

import logging
from pathlib import Path
import re
import time
from typing import Any

from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

REFRESH = {"avatar": 86400, "icon": 30 * 86400}   # seconds before asking the console again
NOT_GAMES = {"nx-hbmenu", "hbmenu", "Homebrew Menu", "NX Control"}
RETRY_AFTER_FAILURE = 3600   # seconds before asking again for an image that failed


def _path(hass: HomeAssistant, kind: str, console_id: str, item_id: str) -> Path:
    return Path(hass.config.path(".storage", "nx_control_images")) / f"{kind}_{console_id}_{item_id.lower()}.jpg"


def _valid(kind: str, console_id: str, item_id: str) -> bool:
    return kind in REFRESH and bool(re.fullmatch(r"[0-9a-fA-F]{8,32}", console_id)) \
        and bool(re.fullmatch(r"[0-9a-fA-F]{16,32}", item_id))


def _coordinator(hass: HomeAssistant, console_id: str):
    return next((e.runtime_data for e in hass.config_entries.async_loaded_entries(DOMAIN)
                 if e.unique_id == console_id), None)


async def async_get_image(hass: HomeAssistant, kind: str, console_id: str, item_id: str,
                          *, refresh_only: bool = False, console_ok: bool = False) -> bytes | None:
    """Cached image; asks the console when it is missing or old. Old copies are kept when it is off."""
    if not _valid(kind, console_id, item_id):
        return None
    path = _path(hass, kind, console_id, item_id)

    def _read() -> tuple[bytes | None, bool]:
        if not path.exists():
            return None, False
        return path.read_bytes(), time.time() - path.stat().st_mtime < REFRESH[kind]

    cached, fresh = await hass.async_add_executor_job(_read)
    if fresh:
        return None if refresh_only else cached
    coordinator = _coordinator(hass, console_id)
    data = None
    failed = hass.data.setdefault("nx_control_image_failures", {})
    key = f"{kind}_{console_id}_{item_id.lower()}"
    recently_failed = time.time() - failed.get(key, 0) < RETRY_AFTER_FAILURE
    if coordinator is not None and (console_ok or coordinator.online) and not recently_failed:
        data = await coordinator.client.image("icons" if kind == "icon" else "avatars", item_id)
        if data:
            failed.pop(key, None)
        else:
            failed[key] = time.time()   # do not keep asking the console for an image it cannot send
    if data:
        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        await hass.async_add_executor_job(_write)
        return data
    return cached


async def async_prefetch(hass: HomeAssistant, coordinator, status: dict[str, Any],
                         usage: list[dict[str, Any]]) -> None:
    """Download the icons of the games in the reports and every player's avatar."""
    console_id = coordinator.config_entry.unique_id or ""
    wanted = [("avatar", str(p.get("id") or "")) for p in status.get("profiles", [])]
    seen: set[str] = set()
    for item in usage:
        pid = str(item.get("program_id") or "")
        if pid and pid not in seen and item.get("title") not in NOT_GAMES:
            seen.add(pid)
            wanted.append(("icon", pid))
    fetched = 0
    for kind, item_id in wanted:
        if item_id and await async_get_image(hass, kind, console_id, item_id, refresh_only=True, console_ok=True):
            fetched += 1
    if fetched:
        _LOGGER.debug("Cached %d NX Control images", fetched)
