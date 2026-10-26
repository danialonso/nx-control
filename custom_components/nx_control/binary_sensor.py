"""Binary sensors: is a profile playing right now."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import PLAYING_STATES
from .entity import NXControlEntity, NXControlProfileEntity, add_profile_entities


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities([ConsoleOnlineBinarySensor(coordinator)])
    add_profile_entities(entry, coordinator, async_add_entities,
                         lambda profile: [PlayingBinarySensor(coordinator, profile)])


class PlayingBinarySensor(NXControlProfileEntity, BinarySensorEntity):
    """On while the profile is playing a game."""

    _attr_translation_key = "playing"
    _attr_icon = "mdi:gamepad-variant"

    def __init__(self, coordinator, profile) -> None:
        super().__init__(coordinator, profile, "playing")
        self._attr_translation_placeholders = {"profile": self._profile_name}

    @property
    def is_on(self) -> bool:
        return (self.profile or {}).get("state") in PLAYING_STATES

    @property
    def extra_state_attributes(self):
        session = (self.coordinator.data or {}).get("session", {})
        if not self.is_on:
            return {}
        return {"game": session.get("title") or session.get("program_id")}


class ConsoleOnlineBinarySensor(NXControlEntity, BinarySensorEntity):
    """On while the console answers (off or asleep otherwise)."""

    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "online")

    @property
    def is_on(self) -> bool:
        return self.coordinator.online

    @property
    def extra_state_attributes(self):
        return {"last_seen": (self.coordinator.data or {}).get("last_seen")}
