"""Phone notifications for time requests (Home Assistant app), with Approve and Deny buttons.

Every phone chosen in the integration options gets the request. When someone answers (from a phone,
the card, the console or an automation), the request disappears from every phone and the others are
told who answered and how.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.util import slugify

from .const import CONF_NOTIFY_DEVICES, CONF_NOTIFY_OPEN, CONF_NOTIFY_RESULTS, DOMAIN, PANEL_URL

_LOGGER = logging.getLogger(__name__)

ACTION_APPROVE = "NXC_APPROVE"
ACTION_DENY = "NXC_DENY"
FROM_CONSOLE = "console"

TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "test_title": "🎮 NX Control is ready",
        "test_body": "This phone will get NX Control notifications, for example when someone asks for more play time.",
        "asks": "🎮 {profile} asks for {amount} more",
        "body": "More play time requested on the Nintendo Switch.",
        "approve": "Approve", "deny": "Deny",
        "approved": "✅ {who} approved {amount} for {profile}",
        "denied": "❌ {who} denied {profile}'s request",
        "approved_console": "✅ {amount} for {profile} approved on the console",
        "denied_console": "❌ {profile}'s request was denied on the console",
    },
    "es": {
        "test_title": "🎮 NX Control está listo",
        "test_body": "Este móvil recibirá los avisos de NX Control, por ejemplo cuando alguien pida más tiempo de juego.",
        "asks": "🎮 {profile} pide {amount} más",
        "body": "Solicitud de más tiempo de juego en la Nintendo Switch.",
        "approve": "Aprobar", "deny": "Rechazar",
        "approved": "✅ {who} ha aprobado {amount} para {profile}",
        "denied": "❌ {who} ha rechazado la solicitud de {profile}",
        "approved_console": "✅ Aprobados {amount} para {profile} desde la consola",
        "denied_console": "❌ Rechazada la solicitud de {profile} desde la consola",
    },
    "fr": {
        "test_title": "🎮 NX Control est prêt",
        "test_body": "Ce téléphone recevra les notifications de NX Control, par exemple quand quelqu'un demande plus de temps de jeu.",
        "asks": "🎮 {profile} demande {amount} de plus",
        "body": "Demande de temps de jeu supplémentaire sur la Nintendo Switch.",
        "approve": "Accepter", "deny": "Refuser",
        "approved": "✅ {who} a accordé {amount} à {profile}",
        "denied": "❌ {who} a refusé la demande de {profile}",
        "approved_console": "✅ {amount} accordées à {profile} depuis la console",
        "denied_console": "❌ Demande de {profile} refusée depuis la console",
    },
    "de": {
        "test_title": "🎮 NX Control ist bereit",
        "test_body": "Dieses Handy erhält die Benachrichtigungen von NX Control, zum Beispiel wenn jemand um mehr Spielzeit bittet.",
        "asks": "🎮 {profile} bittet um {amount} mehr",
        "body": "Anfrage nach mehr Spielzeit auf der Nintendo Switch.",
        "approve": "Genehmigen", "deny": "Ablehnen",
        "approved": "✅ {who} hat {profile} {amount} genehmigt",
        "denied": "❌ {who} hat die Anfrage von {profile} abgelehnt",
        "approved_console": "✅ {amount} für {profile} an der Konsole genehmigt",
        "denied_console": "❌ Anfrage von {profile} an der Konsole abgelehnt",
    },
    "it": {
        "test_title": "🎮 NX Control è pronto",
        "test_body": "Questo telefono riceverà le notifiche di NX Control, ad esempio quando qualcuno chiede più tempo di gioco.",
        "asks": "🎮 {profile} chiede {amount} in più",
        "body": "Richiesta di altro tempo di gioco sulla Nintendo Switch.",
        "approve": "Approva", "deny": "Rifiuta",
        "approved": "✅ {who} ha approvato {amount} per {profile}",
        "denied": "❌ {who} ha rifiutato la richiesta di {profile}",
        "approved_console": "✅ Approvati {amount} per {profile} dalla console",
        "denied_console": "❌ Richiesta di {profile} rifiutata dalla console",
    },
    "pt": {
        "test_title": "🎮 O NX Control está pronto",
        "test_body": "Este telemóvel vai receber os avisos do NX Control, por exemplo quando alguém pedir mais tempo de jogo.",
        "asks": "🎮 {profile} pede mais {amount}",
        "body": "Pedido de mais tempo de jogo na Nintendo Switch.",
        "approve": "Aprovar", "deny": "Recusar",
        "approved": "✅ {who} aprovou {amount} para {profile}",
        "denied": "❌ {who} recusou o pedido de {profile}",
        "approved_console": "✅ Aprovados {amount} para {profile} na consola",
        "denied_console": "❌ Pedido de {profile} recusado na consola",
    },
}


def amount(minutes: int) -> str:
    """15 min, 1 h, 1 h 30 min."""
    if minutes >= 60:
        return f"{minutes // 60} h" + (f" {minutes % 60} min" if minutes % 60 else "")
    return f"{minutes} min"


def phones(hass: HomeAssistant) -> dict[str, str]:
    """Phones with the Home Assistant app: notify service name -> "Device (user)"."""
    out: dict[str, str] = {}
    for entry in hass.config_entries.async_entries("mobile_app"):
        name = entry.data.get("device_name") or entry.title
        if not name:
            continue
        service = f"mobile_app_{slugify(name)}"
        out[service] = name
    return out


def phones_of_user(hass: HomeAssistant, user_id: str | None) -> set[str]:
    if not user_id:
        return set()
    return {
        f"mobile_app_{slugify(e.data.get('device_name') or e.title)}"
        for e in hass.config_entries.async_entries("mobile_app")
        if e.data.get("user_id") == user_id
    }


CARD_TYPE = "custom:nx-control-card"


def _has_card(node: Any) -> bool:
    if isinstance(node, dict):
        return node.get("type") == CARD_TYPE or any(_has_card(v) for v in node.values())
    if isinstance(node, list):
        return any(_has_card(v) for v in node)
    return False


async def async_find_card_page(hass: HomeAssistant) -> str | None:
    """Path of the first dashboard view with the NX Control card, e.g. /lovelace/gaming."""
    lovelace = hass.data.get("lovelace")
    dashboards = getattr(lovelace, "dashboards", None)
    if dashboards is None and isinstance(lovelace, dict):
        dashboards = lovelace.get("dashboards")
    if not isinstance(dashboards, dict):
        return None
    # The default dashboard first, then the others
    for url_path in sorted(dashboards, key=lambda k: (k is not None, str(k))):
        try:
            config = await dashboards[url_path].async_load(False)
        except Exception:  # noqa: BLE001 - dashboards without a saved config (auto-generated)
            continue
        views = config.get("views") if isinstance(config, dict) else None
        for index, view in enumerate(views or []):
            if isinstance(view, dict) and _has_card(view):
                return f"/{url_path or 'lovelace'}/{view.get('path') or index}"
    return None


def texts(hass: HomeAssistant) -> dict[str, str]:
    lang = (hass.config.language or "en").split("-")[0].lower()
    return TEXTS.get(lang, TEXTS["en"])


async def async_notify_page(hass: HomeAssistant, options: dict[str, Any] | None = None) -> str | None:
    """Page opened when tapping a notification: the one chosen in the options, the NX Control page in
    the sidebar, or the dashboard view that has the NX Control card (found automatically)."""
    chosen = ((options or {}).get(CONF_NOTIFY_OPEN) or "").strip()
    if chosen:
        return chosen if chosen.startswith("/") else f"/{chosen}"
    if hass.data.get(DOMAIN, {}).get("panel"):
        return f"/{PANEL_URL}"
    try:
        return await async_find_card_page(hass)
    except Exception as err:  # noqa: BLE001 - never block a notification because of this
        _LOGGER.debug("Could not find the dashboard with the NX Control card: %s", err)
        return None


async def async_send_test(hass: HomeAssistant, services: list[str],
                          options: dict[str, Any] | None = None) -> list[str]:
    """Send a test notification to the chosen phones; tapping it opens the same page as a real
    time request. Returns the phones that failed."""
    t = texts(hass)
    page = await async_notify_page(hass, options)
    data: dict[str, Any] = {"tag": "nxc_test", "group": "nx_control", "channel": "NX Control"}
    if page:
        data.update({"url": page, "clickAction": page})          # iPhone / Android
    failed = []
    for service in services:
        try:
            await hass.services.async_call("notify", service, {
                "title": t["test_title"], "message": t["test_body"], "data": data,
            }, blocking=True)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Test notification to %s failed: %s", service, err)
            failed.append(service)
    return failed


async def async_phone_options(hass: HomeAssistant, current: list[str] | None = None) -> list[dict[str, str]]:
    """Phones with the Home Assistant app, as options for a selector: "iPhone de Inma (Inma)"."""
    found = phones(hass)
    current = current or []
    options = []
    for entry in hass.config_entries.async_entries("mobile_app"):
        name = entry.data.get("device_name") or entry.title
        service = next((s for s, n in found.items() if n == name), None)
        if not service:
            continue
        label = found[service]
        if (user_id := entry.data.get("user_id")) and (user := await hass.auth.async_get_user(user_id)):
            if user.name and user.name.lower() not in label.lower():
                label = f"{label} ({user.name})"
        options.append({"value": service, "label": label})
    for service in current:                       # phones chosen earlier that are gone, so they can be unticked
        if service not in found:
            options.append({"value": service, "label": service})
    return options


class NXControlNotifier:
    """Sends, updates and clears the time request notifications of one console."""

    def __init__(self, hass: HomeAssistant, entry, coordinator) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._requests: dict[str, dict[str, Any]] = {}     # pending requests we notified about
        self._answered_by: dict[str, str | None] = {}      # request id -> HA user id (None = unknown user)

    # ---------------------------------------------------------------- settings
    def _targets(self) -> list[str]:
        wanted = self.entry.options.get(CONF_NOTIFY_DEVICES) or []
        return [s for s in wanted if self.hass.services.has_service("notify", s)]

    def _t(self) -> dict[str, str]:
        return texts(self.hass)

    def _tag(self, request_id: str) -> str:
        return f"nxc_{self.entry.entry_id}_{request_id}"

    async def _send(self, service: str, data: dict[str, Any]) -> None:
        try:
            await self.hass.services.async_call("notify", service, data, blocking=True)
        except Exception as err:  # noqa: BLE001 - one phone failing must not stop the others
            _LOGGER.warning("Could not notify %s: %s", service, err)

    # ---------------------------------------------------------------- events from the coordinator
    async def async_new_request(self, request: dict[str, Any], profile_name: str) -> None:
        req_id = str(request.get("id"))
        minutes = int(request.get("seconds", 0)) // 60
        self._requests[req_id] = {"profile": profile_name, "minutes": minutes}
        targets = self._targets()
        if not targets:
            return
        t = self._t()
        page = await self._page()
        message = (request.get("message") or "").strip()
        if message in ("touch", "ZL+ZR", "app", "overlay"):     # how it was asked, not a message
            message = ""
        data = {
            "title": t["asks"].format(profile=profile_name, amount=amount(minutes)),
            "message": f"“{message}”" if message else t["body"],
            "data": {
                "tag": self._tag(req_id),
                "group": "nx_control",
                "actions": [
                    {"action": f"{ACTION_APPROVE}-{self.entry.entry_id}-{req_id}", "title": t["approve"]},
                    {"action": f"{ACTION_DENY}-{self.entry.entry_id}-{req_id}", "title": t["deny"],
                     "destructive": True},
                ],
                # iPhone: shown even in Focus modes. Android: right away, in its own channel.
                "push": {"interruption-level": "time-sensitive"},
                "priority": "high",
                "ttl": 0,
                "channel": "NX Control",
                **({"url": page, "clickAction": page} if page else {}),   # iPhone / Android
            },
        }
        for service in targets:
            await self._send(service, data)

    async def async_resolved(self, request: dict[str, Any] | None, req_id: str) -> None:
        """The request is no longer pending: clear it everywhere and tell the others."""
        info = self._requests.pop(req_id, None)
        answered = req_id in self._answered_by
        user_id = self._answered_by.pop(req_id, None)
        targets = self._targets()
        if not targets or info is None:
            return
        status = (request or {}).get("status")
        tag = self._tag(req_id)
        clear = {"message": "clear_notification", "data": {"tag": tag}}
        if status not in ("approved", "denied") or not self.entry.options.get(CONF_NOTIFY_RESULTS, True):
            for service in targets:
                await self._send(service, clear)
            return

        t = self._t()
        minutes = int((request or {}).get("seconds", info["minutes"] * 60)) // 60
        if answered:
            who = await self._user_name(user_id)
            text = t[status].format(who=who, profile=info["profile"], amount=amount(minutes))
        else:
            text = t[f"{status}_console"].format(profile=info["profile"], amount=amount(minutes))
        result = {"title": "NX Control", "message": text, "data": {"tag": tag, "group": "nx_control"}}
        own = phones_of_user(self.hass, user_id)
        for service in targets:
            # The person who answered just sees the notification go away; the others are told.
            await self._send(service, clear if service in own else result)

    async def _page(self) -> str | None:
        """Page opened when tapping the notification (see async_notify_page)."""
        return await async_notify_page(self.hass, self.entry.options)

    def answered_by(self, req_id: str, user_id: str | None) -> None:
        """Remember who answered a request from Home Assistant (card, phone or action)."""
        self._answered_by[str(req_id)] = user_id

    async def _user_name(self, user_id: str | None) -> str:
        if user_id and (user := await self.hass.auth.async_get_user(user_id)) and user.name:
            return user.name
        return "Home Assistant"

    # ---------------------------------------------------------------- buttons on the phone
    @callback
    def async_listen(self) -> None:
        self.entry.async_on_unload(
            self.hass.bus.async_listen("mobile_app_notification_action", self._on_action))

    async def _on_action(self, event: Event) -> None:
        action = str(event.data.get("action") or "")
        parts = action.split("-", 2)
        if len(parts) != 3 or parts[0] not in (ACTION_APPROVE, ACTION_DENY) or parts[1] != self.entry.entry_id:
            return
        req_id = parts[2]
        self.answered_by(req_id, event.context.user_id)
        from .api import NXControlError
        try:
            if parts[0] == ACTION_APPROVE:
                await self.coordinator.client.approve(req_id)
            else:
                await self.coordinator.client.deny(req_id)
        except NXControlError as err:
            # Already answered by someone else, or the console is off
            _LOGGER.info("Could not answer time request %s: %s", req_id, err)
            self._answered_by.pop(req_id, None)
        await self.coordinator.async_request_refresh()
