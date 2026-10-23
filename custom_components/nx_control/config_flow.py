"""Config flow: discovery (zeroconf) or manual host, then pairing code."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
except ImportError:  # Home Assistant < 2025.2
    from homeassistant.components.zeroconf import ZeroconfServiceInfo

from .api import NXControlAuthError, NXControlClient, NXControlError
from .const import CONF_TOKEN, DEFAULT_PORT, DOMAIN


class NXControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NX Control."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._port: int = DEFAULT_PORT
        self._info: dict[str, Any] = {}

    def _client(self) -> NXControlClient:
        return NXControlClient(async_get_clientsession(self.hass), self._host, self._port)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            try:
                self._info = await self._client().info()
            except NXControlError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(self._info["console_id"])
                self._abort_if_unique_id_configured(updates={CONF_HOST: self._host, CONF_PORT: self._port})
                return await self.async_step_pair()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }),
            errors=errors,
        )

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        self._host = discovery_info.host
        self._port = discovery_info.port or DEFAULT_PORT
        console_id = discovery_info.properties.get("id")
        if not console_id:
            return self.async_abort(reason="not_supported")
        await self.async_set_unique_id(console_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: self._host, CONF_PORT: self._port})
        try:
            self._info = await self._client().info()
        except NXControlError:
            return self.async_abort(reason="cannot_connect")
        self.context["title_placeholders"] = {"name": self._title()}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return await self.async_step_pair()
        return self.async_show_form(
            step_id="discovery_confirm", description_placeholders={"name": self._title()}
        )

    async def async_step_pair(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = self._client()
            try:
                token = await client.pair(user_input["code"].strip())
            except NXControlAuthError:
                errors["base"] = "invalid_code"
            except NXControlError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=self._title(),
                    data={CONF_HOST: self._host, CONF_PORT: self._port, CONF_TOKEN: token},
                )
        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({vol.Required("code"): str}),
            description_placeholders={"name": self._title()},
            errors=errors,
        )

    def _title(self) -> str:
        return self._info.get("console_name") or "Nintendo Switch"
