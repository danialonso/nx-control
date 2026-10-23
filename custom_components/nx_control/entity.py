"""Base entity for NX Control."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NXControlCoordinator


class NXControlEntity(CoordinatorEntity[NXControlCoordinator]):
    """Common device info."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NXControlCoordinator, key: str) -> None:
        super().__init__(coordinator)
        console_id = coordinator.config_entry.unique_id
        self._attr_unique_id = f"{console_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, console_id)},
            name=coordinator.config_entry.title,
            manufacturer="NX Control",
            model="Nintendo Switch",
        )


class NXControlProfileEntity(NXControlEntity):
    """Entity bound to one profile."""

    def __init__(self, coordinator: NXControlCoordinator, profile: dict[str, Any], key: str) -> None:
        self._profile_id = profile["id"]
        super().__init__(coordinator, f"{self._profile_id}_{key}")
        self._profile_name = profile.get("name", self._profile_id[:8])

    @property
    def profile(self) -> dict[str, Any] | None:
        for p in (self.coordinator.data or {}).get("profiles", []):
            if p.get("id") == self._profile_id:
                return p
        return None

    @property
    def available(self) -> bool:
        return super().available and self.profile is not None
