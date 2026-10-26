"""Switch: lock the console."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import NXControlActionMixin, NXControlEntity, NXControlProfileEntity, add_profile_entities


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities([ConsoleLockSwitch(coordinator)])
    add_profile_entities(
        entry, coordinator, async_add_entities,
        lambda profile: [ProfileBlockSwitch(coordinator, profile)],
        condition=lambda profile: profile.get("mode") in ("supervised", "self"),
    )


class ConsoleLockSwitch(NXControlActionMixin, NXControlEntity, SwitchEntity):
    _attr_translation_key = "console_lock"
    _attr_icon = "mdi:lock"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "console_lock")

    @property
    def extra_state_attributes(self):
        return {"nx_control_console_id": self.coordinator.config_entry.unique_id}

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get("console", {}).get("locked"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_locked(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_locked(False)
        await self.coordinator.async_request_refresh()


class ProfileBlockSwitch(NXControlActionMixin, NXControlProfileEntity, SwitchEntity):
    """Blocks a profile until the end of the day (the "stop playing now" button)."""

    _attr_translation_key = "profile_block"
    _attr_icon = "mdi:gamepad-variant-outline"

    def __init__(self, coordinator, profile) -> None:
        super().__init__(coordinator, profile, "block")
        self._attr_translation_placeholders = {"profile": self._profile_name}

    @property
    def is_on(self) -> bool:
        p = self.profile or {}
        return bool(p.get("profile_blocked", p.get("blocked")))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.block(self._profile_id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.unblock(self._profile_id)
        await self.coordinator.async_request_refresh()
