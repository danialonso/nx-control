"""Config flow: discovery (zeroconf) or manual host, then pairing code."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector, SelectOptionDict, SelectSelector, SelectSelectorConfig, SelectSelectorMode, TextSelector,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
except ImportError:  # Home Assistant < 2025.2
    from homeassistant.components.zeroconf import ZeroconfServiceInfo

from .api import NXControlAuthError, NXControlClient, NXControlError, NXControlRateLimitError
from .const import (
    CONF_NOTIFY_DEVICES, CONF_NOTIFY_OPEN, CONF_NOTIFY_RESULTS, CONF_NOTIFY_TEST, CONF_SIDEBAR, CONF_TOKEN,
    DEFAULT_PORT, DOMAIN, PANEL_URL,
)

WIKI = "https://github.com/danialonso/nx-control/wiki"


def _phones_selector(options: list[dict[str, str]]) -> SelectSelector:
    return SelectSelector(SelectSelectorConfig(
        options=[SelectOptionDict(value=o["value"], label=o["label"]) for o in options],
        multiple=True, mode=SelectSelectorMode.LIST))


class NXControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NX Control."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return NXControlOptionsFlow()

    def __init__(self) -> None:
        self._host: str | None = None
        self._port: int = DEFAULT_PORT
        self._info: dict[str, Any] = {}
        self._token: str | None = None
        self._options: dict[str, Any] = {CONF_NOTIFY_DEVICES: [], CONF_NOTIFY_RESULTS: True, CONF_SIDEBAR: True}

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
                # Manual setup takes over a pending "Discovered" entry for the same console
                # instead of aborting with "already in progress".
                await self.async_set_unique_id(self._info["console_id"], raise_on_progress=False)
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

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Change the console address (for example after the router gave it a new IP)."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            try:
                info = await self._client().info()
            except NXControlError:
                errors["base"] = "cannot_connect"
            else:
                if info.get("console_id") != entry.unique_id:
                    errors["base"] = "wrong_console"
                else:
                    return self.async_update_reload_and_abort(
                        entry, data_updates={CONF_HOST: self._host, CONF_PORT: self._port})
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=entry.data.get(CONF_PORT, DEFAULT_PORT)): int,
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
            except NXControlRateLimitError:
                errors["base"] = "too_many_attempts"
            except NXControlError:
                errors["base"] = "cannot_connect"
            else:
                self._token = token
                return await self.async_step_notifications()
        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({vol.Required("code"): str}),
            description_placeholders={"name": self._title()},
            errors=errors,
        )

    # ---------------------------------------------------------------- guided setup after pairing
    async def async_step_notifications(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Step 3: which phones get the time requests (with Approve / Deny)."""
        from .notify import async_phone_options, async_send_test
        options = await async_phone_options(self.hass, self._options[CONF_NOTIFY_DEVICES])
        if user_input is not None:
            self._options[CONF_NOTIFY_DEVICES] = user_input.get(CONF_NOTIFY_DEVICES, [])
            self._options[CONF_NOTIFY_RESULTS] = user_input.get(CONF_NOTIFY_RESULTS, True)
            if user_input.get(CONF_NOTIFY_TEST) and self._options[CONF_NOTIFY_DEVICES]:
                await async_send_test(self.hass, self._options[CONF_NOTIFY_DEVICES], self._options)
                return await self.async_step_notifications_test()
            return await self.async_step_sidebar()
        if not options:
            # No phone with the Home Assistant app yet: explain and go on
            return self.async_show_form(step_id="notifications_none", data_schema=vol.Schema({}))
        return self.async_show_form(
            step_id="notifications",
            data_schema=vol.Schema({
                vol.Optional(CONF_NOTIFY_DEVICES, default=self._options[CONF_NOTIFY_DEVICES]): _phones_selector(options),
                vol.Optional(CONF_NOTIFY_RESULTS, default=self._options[CONF_NOTIFY_RESULTS]): BooleanSelector(),
                vol.Optional(CONF_NOTIFY_TEST, default=True): BooleanSelector(),
            }),
        )

    async def async_step_notifications_none(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self.async_step_sidebar()

    async def async_step_notifications_test(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """The test notification was sent: did it arrive?"""
        return self.async_show_menu(step_id="notifications_test", menu_options=["sidebar", "notifications"])

    async def async_step_sidebar(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Step 4: the NX Control page in the sidebar (skipped if another console already shows it)."""
        if user_input is not None:
            self._options[CONF_SIDEBAR] = user_input.get(CONF_SIDEBAR, True)
            return self._finish()
        if self.hass.data.get(DOMAIN, {}).get("panel"):
            return self._finish()
        return self.async_show_form(
            step_id="sidebar",
            data_schema=vol.Schema({vol.Optional(CONF_SIDEBAR, default=True): BooleanSelector()}),
        )

    def _finish(self) -> ConfigFlowResult:
        """Create the entry; the success dialog sums up what was set up and explains the card."""
        phones = len(self._options[CONF_NOTIFY_DEVICES])
        sidebar = self._options[CONF_SIDEBAR] or bool(self.hass.data.get(DOMAIN, {}).get("panel"))
        return self.async_create_entry(
            title=self._title(),
            data={CONF_HOST: self._host, CONF_PORT: self._port, CONF_TOKEN: self._token},
            options=dict(self._options),
            description="done",
            description_placeholders={
                "name": self._title(),
                "phones": str(phones),
                "page": f"/{PANEL_URL}" if sidebar else "-",
                "wiki": WIKI,
            },
        )

    def _title(self) -> str:
        return self._info.get("console_name") or "Nintendo Switch"


class NXControlOptionsFlow(OptionsFlow):
    """Sidebar page and phone notifications (the same choices as during setup)."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        from .notify import async_find_card_page, async_phone_options, async_send_test
        if user_input is not None:
            test = user_input.pop(CONF_NOTIFY_TEST, False)
            if test and user_input.get(CONF_NOTIFY_DEVICES):
                await async_send_test(self.hass, user_input[CONF_NOTIFY_DEVICES], user_input)
            return self.async_create_entry(data=user_input)

        current = list(self.config_entry.options.get(CONF_NOTIFY_DEVICES, []))
        options = await async_phone_options(self.hass, current)
        found_page = f"/{PANEL_URL}" if self.hass.data.get(DOMAIN, {}).get("panel") \
            else await async_find_card_page(self.hass)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_SIDEBAR,
                             default=self.config_entry.options.get(CONF_SIDEBAR, True)): BooleanSelector(),
                vol.Optional(CONF_NOTIFY_DEVICES, default=current): _phones_selector(options),
                vol.Optional(CONF_NOTIFY_RESULTS,
                             default=self.config_entry.options.get(CONF_NOTIFY_RESULTS, True)): BooleanSelector(),
                vol.Optional(CONF_NOTIFY_TEST, default=False): BooleanSelector(),
                vol.Optional(CONF_NOTIFY_OPEN,
                             description={"suggested_value": self.config_entry.options.get(CONF_NOTIFY_OPEN, "")}): TextSelector(),
            }),
            description_placeholders={"found": found_page or "-"},
        )
