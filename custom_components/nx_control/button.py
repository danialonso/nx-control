"""Buttons: add extra time to a profile."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import NXControlActionMixin, NXControlProfileEntity, add_profile_entities


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    # Extra time only makes sense for profiles with limits
    add_profile_entities(
        entry, coordinator, async_add_entities,
        lambda profile: [GrantTimeButton(coordinator, profile, m) for m in (15, 30)],
        condition=lambda profile: profile.get("mode") in ("supervised", "self"),
    )


class GrantTimeButton(NXControlActionMixin, NXControlProfileEntity, ButtonEntity):
    _attr_translation_key = "grant_time"
    _attr_icon = "mdi:timer-plus"

    def __init__(self, coordinator, profile, minutes: int) -> None:
        super().__init__(coordinator, profile, f"grant_{minutes}")
        self._minutes = minutes
        self._attr_translation_placeholders = {"profile": self._profile_name, "minutes": str(minutes)}

    async def async_press(self) -> None:
        await self.coordinator.client.grant(self._profile_id, self._minutes * 60, "Home Assistant")
        await self.coordinator.async_request_refresh()
