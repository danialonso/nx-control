"""NX Control integration for Home Assistant."""
from __future__ import annotations

import json
import logging
from pathlib import Path
import re
import shutil
import time

from aiohttp import web

import voluptuous as vol

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import NXControlClient, NXControlConflictError, NXControlError
from .const import (
    ATTR_MESSAGE, ATTR_MINUTES, ATTR_PROFILE_ID, ATTR_REQUEST_ID, CARD_URL, CONF_SIDEBAR, CONF_TOKEN, DOMAIN,
    IMAGE_URL, PANEL_URL,
    SERVICE_APPROVE_REQUEST, SERVICE_BLOCK_PROFILE, SERVICE_DENY_REQUEST, SERVICE_GRANT_TIME,
    SERVICE_UNBLOCK_PROFILE,
)
from .coordinator import NXControlCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR, Platform.SWITCH]
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
BLOCK_SCHEMA = vol.Schema({
    vol.Optional("console_id"): cv.string,
    vol.Required(ATTR_PROFILE_ID): cv.string,
    vol.Optional(ATTR_MINUTES): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
})
UNBLOCK_SCHEMA = vol.Schema({
    vol.Optional("console_id"): cv.string,
    vol.Required(ATTR_PROFILE_ID): cv.string,
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


class NXControlImageView(HomeAssistantView):
    """Game icons and user avatars, fetched from the console once and cached on disk.

    Public on purpose (like entity pictures): <img> tags cannot send credentials, and the
    images are only game covers and profile pictures.
    """

    url = IMAGE_URL + "/{kind}/{console_id}/{item_id}"
    name = "api:nx_control:image"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, kind: str, console_id: str, item_id: str) -> web.StreamResponse:
        from .images import async_get_image
        data = await async_get_image(self.hass, kind, console_id, item_id)
        if not data:
            return web.Response(status=404)
        return web.Response(body=data, content_type="image/jpeg", headers={"Cache-Control": "max-age=3600"})


class NXControlVersionView(HomeAssistantView):
    """Version of the integration, so the card can tell when the page runs an older copy of itself."""

    url = "/api/nx_control/version"
    name = "api:nx_control:version"
    requires_auth = True

    def __init__(self, version: str) -> None:
        self._version = version

    async def get(self, request: web.Request) -> web.Response:
        return self.json({"version": self._version})


LOCAL_DIR = "nx_control"            # inside <config>/www, served as /local/nx_control/
LOCAL_URL = f"/local/{LOCAL_DIR}/nx-control-card.js"


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve the NX Control card and make every dashboard load it (no manual resource needed).

    The card is loaded in two ways:
    - As a dashboard resource served from /local (a copy in <config>/www/nx_control/). Home Assistant
      serves /local from the very start, so the card is there even when the app opens a dashboard
      while Home Assistant is still starting and NX Control is not loaded yet.
    - With add_extra_js_url, from /nx_control/, as a fallback (YAML dashboards, or the first start
      after installing, when /local may not be available yet).
    """
    from homeassistant.components.frontend import add_extra_js_url
    from homeassistant.components.http import StaticPathConfig

    path = Path(__file__).parent / "frontend" / "nx-control-card.js"
    www = Path(hass.config.path("www"))

    def _prepare() -> tuple[str, str, bool]:
        manifest = json.loads((Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))
        version = str(manifest.get("version", "0"))
        cache_key = f"{version}-{int(path.stat().st_mtime)}"
        # /local is only served when <config>/www already existed when Home Assistant started
        local_ok = www.is_dir()
        try:
            dest = www / LOCAL_DIR / "nx-control-card.js"
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists() or dest.read_bytes() != path.read_bytes():
                shutil.copyfile(path, dest)
        except OSError as err:
            _LOGGER.warning("Could not copy the NX Control card to %s: %s", www, err)
            local_ok = False
        return version, cache_key, local_ok

    version, cache_key, local_ok = await hass.async_add_executor_job(_prepare)
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(path), False)])
    hass.http.register_view(NXControlImageView(hass))
    hass.http.register_view(NXControlVersionView(version))
    add_extra_js_url(hass, f"{CARD_URL}?v={cache_key}")
    hass.data.setdefault(DOMAIN, {})["card_module"] = f"{CARD_URL}?v={cache_key}"

    resource_url = f"{LOCAL_URL}?v={cache_key}" if local_ok else f"{CARD_URL}?v={cache_key}"
    from homeassistant.helpers.start import async_at_started

    async def _resource(_hass: HomeAssistant) -> None:
        await _async_manage_card_resource(hass, resource_url)

    async_at_started(hass, _resource)


def _lovelace_resources(hass: HomeAssistant):
    lovelace = hass.data.get("lovelace")
    resources = getattr(lovelace, "resources", None)
    if resources is None and isinstance(lovelace, dict):
        resources = lovelace.get("resources")
    if resources is None or not hasattr(resources, "async_create_item"):
        return None     # YAML mode: resources can only be changed by hand
    return resources


async def _async_manage_card_resource(hass: HomeAssistant, url: str | None) -> None:
    """Keep exactly one dashboard resource for the NX Control card, pointing to this version.

    With url=None, remove it (the integration is being removed).
    """
    try:
        resources = _lovelace_resources(hass)
        if resources is None:
            return
        if not getattr(resources, "loaded", True):
            await resources.async_load()
            resources.loaded = True
        mine = None
        for item in list(resources.async_items()):
            item_url = str(item.get("url", ""))
            if "nx-control-card" not in item_url or "id" not in item:
                continue
            if url and mine is None:
                mine = item
                if item_url != url or item.get("type") != "module":
                    await resources.async_update_item(item["id"], {"res_type": "module", "url": url})
            else:
                await resources.async_delete_item(item["id"])
                if url:
                    _LOGGER.warning("Removed the extra dashboard resource %s (NX Control manages its card)", item_url)
        if url and mine is None:
            await resources.async_create_item({"res_type": "module", "url": url})
            _LOGGER.info("Added the NX Control card to the dashboard resources")
    except Exception as err:  # noqa: BLE001 - never break the integration because of this
        _LOGGER.debug("Could not manage the dashboard resource of the card: %s", err)


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
                c.notifier.answered_by(call.data[ATTR_REQUEST_ID], call.context.user_id)
                await c.client.approve(call.data[ATTR_REQUEST_ID], minutes * 60 if minutes else None)
            except NXControlConflictError as err:
                await c.async_request_refresh()
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="already_answered") from err
            except NXControlError as err:
                raise HomeAssistantError(str(err)) from err
            await c.async_request_refresh()

    async def deny_request(call: ServiceCall) -> None:
        for c in _coordinators(hass, call.data.get("console_id")):
            try:
                c.notifier.answered_by(call.data[ATTR_REQUEST_ID], call.context.user_id)
                await c.client.deny(call.data[ATTR_REQUEST_ID], call.data[ATTR_MESSAGE])
            except NXControlConflictError as err:
                await c.async_request_refresh()
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="already_answered") from err
            except NXControlError as err:
                raise HomeAssistantError(str(err)) from err
            await c.async_request_refresh()

    async def block_profile(call: ServiceCall) -> None:
        for c in _coordinators(hass, call.data.get("console_id")):
            try:
                await c.client.block(call.data[ATTR_PROFILE_ID], call.data.get(ATTR_MINUTES))
            except NXControlError as err:
                raise HomeAssistantError(str(err)) from err
            await c.async_request_refresh()

    async def unblock_profile(call: ServiceCall) -> None:
        for c in _coordinators(hass, call.data.get("console_id")):
            try:
                await c.client.unblock(call.data[ATTR_PROFILE_ID])
            except NXControlError as err:
                raise HomeAssistantError(str(err)) from err
            await c.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_GRANT_TIME, grant_time, schema=GRANT_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_BLOCK_PROFILE, block_profile, schema=BLOCK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UNBLOCK_PROFILE, unblock_profile, schema=UNBLOCK_SCHEMA)
    await _async_register_card(hass)
    hass.services.async_register(DOMAIN, SERVICE_APPROVE_REQUEST, approve_request, schema=APPROVE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DENY_REQUEST, deny_request, schema=DENY_SCHEMA)
    return True


async def _async_update_panel(hass: HomeAssistant, entry_id_leaving: str | None = None) -> None:
    """Add or remove the NX Control page in the sidebar (/nx-control): the card, full screen."""
    from homeassistant.components import panel_custom
    from homeassistant.components.frontend import async_remove_panel

    data = hass.data.setdefault(DOMAIN, {})
    entries = [e for e in hass.config_entries.async_entries(DOMAIN) if e.entry_id != entry_id_leaving]
    want = any(e.options.get(CONF_SIDEBAR, True) for e in entries)
    have = data.get("panel", False)
    if want and not have:
        try:
            await panel_custom.async_register_panel(
                hass,
                frontend_url_path=PANEL_URL,
                webcomponent_name="nx-control-panel",
                sidebar_title="NX Control",
                sidebar_icon="nxc:family",
                module_url=data.get("card_module", CARD_URL),
                embed_iframe=False,
                require_admin=False,                  # everyone can answer time requests
                config={},
            )
            data["panel"] = True
        except ValueError as err:
            # Another page already uses /nx-control (for example a dashboard made by hand)
            _LOGGER.warning("Could not add the NX Control page to the sidebar: %s. "
                            "Delete the dashboard that uses /%s to get it.", err, PANEL_URL)
    elif have and not want:
        async_remove_panel(hass, PANEL_URL)
        data["panel"] = False


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await _async_update_panel(hass)


async def async_setup_entry(hass: HomeAssistant, entry: NXControlConfigEntry) -> bool:
    client = NXControlClient(
        async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_TOKEN]
    )
    coordinator = NXControlCoordinator(hass, entry, client)
    await coordinator.async_load_cache()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    coordinator.notifier.async_listen()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await _async_update_panel(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NXControlConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await _async_update_panel(hass, entry_id_leaving=entry.entry_id)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """When the last console is removed, remove the card resource and its copy in www."""
    if any(e.entry_id != entry.entry_id for e in hass.config_entries.async_entries(DOMAIN)):
        return
    await _async_manage_card_resource(hass, None)

    def _delete() -> None:
        shutil.rmtree(Path(hass.config.path("www")) / LOCAL_DIR, ignore_errors=True)

    await hass.async_add_executor_job(_delete)
