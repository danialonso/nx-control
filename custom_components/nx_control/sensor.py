"""Sensors for NX Control."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import NXControlEntity, NXControlProfileEntity

STATES = ["idle", "playing", "warning", "grace", "exhausted", "outside_window", "blocked"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [CurrentGameSensor(coordinator), PendingRequestsSensor(coordinator)]
    for profile in coordinator.data.get("profiles", []):
        entities += [
            UsedTodaySensor(coordinator, profile),
            RemainingTodaySensor(coordinator, profile),
            ProfileStateSensor(coordinator, profile),
        ]
    async_add_entities(entities)


class CurrentGameSensor(NXControlEntity, SensorEntity):
    _attr_translation_key = "current_game"
    _attr_icon = "mdi:nintendo-switch"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "current_game")

    @property
    def native_value(self):
        session = (self.coordinator.data or {}).get("session", {})
        if not session.get("active"):
            return None
        return session.get("title") or session.get("program_id")

    @property
    def extra_state_attributes(self):
        session = (self.coordinator.data or {}).get("session", {})
        return {k: session.get(k) for k in ("profile_id", "program_id", "focused", "started_at")}


class PendingRequestsSensor(NXControlEntity, SensorEntity):
    _attr_translation_key = "pending_requests"
    _attr_icon = "mdi:timer-plus-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "pending_requests")

    @property
    def native_value(self):
        return len((self.coordinator.data or {}).get("requests", []))

    @property
    def extra_state_attributes(self):
        return {"requests": (self.coordinator.data or {}).get("requests", [])}


class _DurationSensor(NXControlProfileEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_suggested_unit_of_measurement = UnitOfTime.MINUTES
    _field = ""

    @property
    def native_value(self):
        value = (self.profile or {}).get(self._field)
        return None if value is None or value < 0 else value


class UsedTodaySensor(_DurationSensor):
    _attr_translation_key = "used_today"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _field = "used_today"

    def __init__(self, coordinator, profile) -> None:
        super().__init__(coordinator, profile, "used_today")
        self._attr_translation_placeholders = {"profile": self._profile_name}


class RemainingTodaySensor(_DurationSensor):
    _attr_translation_key = "remaining_today"
    _field = "remaining_today"

    def __init__(self, coordinator, profile) -> None:
        super().__init__(coordinator, profile, "remaining_today")
        self._attr_translation_placeholders = {"profile": self._profile_name}


class ProfileStateSensor(NXControlProfileEntity, SensorEntity):
    _attr_translation_key = "profile_state"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATES

    def __init__(self, coordinator, profile) -> None:
        super().__init__(coordinator, profile, "state")
        self._attr_translation_placeholders = {"profile": self._profile_name}

    @property
    def native_value(self):
        state = (self.profile or {}).get("state", "idle")
        return state if state in STATES else "idle"
