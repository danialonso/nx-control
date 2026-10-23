"""NX Control integration for Home Assistant."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import NXControlClient, NXControlError
from .const import (
    ATTR_MESSAGE, ATTR_MINUTES, ATTR_PROFILE_ID, ATTR_REQUEST_ID, CONF_TOKEN, DOMAIN,
    SERVICE_APPROVE_REQUEST, SERVICE_DENY_REQUEST, SERVICE_GRANT_TIME,
)
from .coordinator import NXControlCoordinator

PLATFORMS = [Platform.BUTTON, Platform.SENSOR, Platform.SWITCH]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type NXControlConfigEntry = ConfigEntry[NXControlCoordinator]

GRANT_SCHEMA = vol.Schema({
    vol.Optional("console_id"): cv.string,
    vol.Required(ATTR_PROFILE_ID): cv.string,
    vol.Required(ATTR_MINUTES): vol.All(vol.Coerce(int), vol.Range(min=1, max=600)),
})
APPROVE_SCHEMA = vol.Schema({
    vol.Optional("console_id"): cv.string,
    vol.Required(ATTR_REQUEST_ID): cv.string,
    vol.Optional(ATTR_MINUTES): vol.All(vol.Coerce(int), vol.Range(min=1, max=600)),
})
DENY_SCHEMA = vol.Schema({
    vol.Optional("console_id"): cv.string,
    vol.Required(ATTR_REQUEST_ID): cv.string,
    vol.Optional(ATTR_MESSAGE, default=""): cv.string,
})


def _coordinators(hass: HomeAssistant, console_id: str | None) -> list[NXControlCoordinator]:
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    result = [e.runtime_data for e in entries if console_id in (None, e.unique_id)]
    if not result:
        raise HomeAssistantError("No NX Control console found")
    return result


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register actions."""

    async def grant_time(call: ServiceCall) -> None:
        for c in _coordinators(hass, call.data.get("console_id")):
            try:
                await c.client.grant(call.data[ATTR_PROFILE_ID], call.data[ATTR_MINUTES] * 60, "Home Assistant")
            except NXControlError as err:
                raise HomeAssistantError(str(err)) from err
            await c.async_request_refresh()

    async def approve_request(call: ServiceCall) -> None:
        minutes = call.data.get(ATTR_MINUTES)
        for c in _coordinators(hass, call.data.get("console_id")):
            try:
                await c.client.approve(call.data[ATTR_REQUEST_ID], minutes * 60 if minutes else None)
            except NXControlError as err:
                raise HomeAssistantError(str(err)) from err
            await c.async_request_refresh()

    async def deny_request(call: ServiceCall) -> None:
        for c in _coordinators(hass, call.data.get("console_id")):
            try:
                await c.client.deny(call.data[ATTR_REQUEST_ID], call.data[ATTR_MESSAGE])
            except NXControlError as err:
                raise HomeAssistantError(str(err)) from err
            await c.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_GRANT_TIME, grant_time, schema=GRANT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_APPROVE_REQUEST, approve_request, schema=APPROVE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DENY_REQUEST, deny_request, schema=DENY_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: NXControlConfigEntry) -> bool:
    client = NXControlClient(
        async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_TOKEN]
    )
    coordinator = NXControlCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NXControlConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
