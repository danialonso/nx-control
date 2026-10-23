"""Buttons: add extra time to a profile."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import NXControlProfileEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GrantTimeButton(coordinator, profile, minutes)
        for profile in coordinator.data.get("profiles", [])
        if profile.get("mode") != "analytics"
        for minutes in (15, 30)
    )


class GrantTimeButton(NXControlProfileEntity, ButtonEntity):
    _attr_translation_key = "grant_time"
    _attr_icon = "mdi:timer-plus"

    def __init__(self, coordinator, profile, minutes: int) -> None:
        super().__init__(coordinator, profile, f"grant_{minutes}")
        self._minutes = minutes
        self._attr_translation_placeholders = {"profile": self._profile_name, "minutes": str(minutes)}

    async def async_press(self) -> None:
        await self.coordinator.client.grant(self._profile_id, self._minutes * 60, "Home Assistant")
        await self.coordinator.async_request_refresh()
