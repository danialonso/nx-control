"""Switch: lock the console."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import NXControlEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([ConsoleLockSwitch(entry.runtime_data)])


class ConsoleLockSwitch(NXControlEntity, SwitchEntity):
    _attr_translation_key = "console_lock"
    _attr_icon = "mdi:lock"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "console_lock")

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get("console", {}).get("locked"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_locked(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_locked(False)
        await self.coordinator.async_request_refresh()
