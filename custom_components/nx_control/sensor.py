"""Sensors for NX Control."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import IMAGE_URL
from .entity import NXControlEntity, NXControlProfileEntity, add_profile_entities

STATES = ["idle", "playing", "warning", "grace", "exhausted", "outside_window", "blocked", "offline"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities([CurrentGameSensor(coordinator), PendingRequestsSensor(coordinator)])
    add_profile_entities(entry, coordinator, async_add_entities, lambda profile: [
        UsedTodaySensor(coordinator, profile),
        RemainingTodaySensor(coordinator, profile),
        ProfileStateSensor(coordinator, profile),
    ])


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
        data = self.coordinator.data or {}
        return {
            "requests": data.get("requests", []),
            "nx_control_console_id": self.coordinator.config_entry.unique_id,
            "nx_control_console_name": self.coordinator.config_entry.title,
            "nx_control_locked": bool(data.get("console", {}).get("locked")),
            "online": self.coordinator.online,
            "last_seen": data.get("last_seen"),
        }


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

    @property
    def extra_state_attributes(self):
        """Everything the NX Control card needs about this profile."""
        p = self.profile or {}
        return {
            "nx_control_profile_id": self._profile_id,
            "nx_control_console_id": self.coordinator.config_entry.unique_id,
            "nx_control_console_name": self.coordinator.config_entry.title,
            "profile_name": p.get("name"),
            "mode": p.get("mode"),
            "used_today": p.get("used_today"),
            "limit_today": p.get("limit_today"),
            "remaining_today": p.get("remaining_today"),
            "in_allowed_window": p.get("in_allowed_window"),
            "blocked": p.get("blocked"),
            "profile_blocked": p.get("profile_blocked"),
            "game": p.get("game_title") or p.get("game_program_id"),
            "game_remaining": p.get("game_remaining"),
            "online": self.coordinator.online,
            "last_seen": (self.coordinator.data or {}).get("last_seen"),
            "avatar": f"{IMAGE_URL}/avatar/{self.coordinator.config_entry.unique_id}/{self._profile_id}",
            "icon_base": f"{IMAGE_URL}/icon/{self.coordinator.config_entry.unique_id}",
            **self.coordinator.report(self._profile_id),
        }
