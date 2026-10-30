"""Async client for the NX Control local API."""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class NXControlError(Exception):
    """Base error."""


class NXControlConnectionError(NXControlError):
    """The console cannot be reached (offline or sleeping)."""


class NXControlAuthError(NXControlError):
    """Invalid token or pairing code."""


class NXControlRateLimitError(NXControlError):
    """Too many wrong pairing codes."""


class NXControlConflictError(NXControlError):
    """The request was already answered (by someone else, or from the console)."""


class NXControlClient:
    """Small wrapper around the REST API (see docs/api.md)."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        token: str | None = None,
    ) -> None:
        self._session = session
        self._base = f"http://{host}:{port}/api/v1"
        self._token = token

    async def _request(self, method: str, path: str, json: dict | None = None) -> Any:
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        try:
            async with asyncio.timeout(10):
                resp = await self._session.request(
                    method, f"{self._base}{path}", json=json, headers=headers
                )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise NXControlConnectionError(str(err)) from err

        if resp.status == 429:
            raise NXControlRateLimitError(await resp.text())
        if resp.status in (401, 403):
            raise NXControlAuthError(await resp.text())
        if resp.status == 409:
            raise NXControlConflictError(await resp.text())
        if resp.status >= 400:
            raise NXControlError(f"{resp.status}: {await resp.text()}")
        if resp.content_type == "application/json":
            return await resp.json()
        return None

    async def info(self) -> dict[str, Any]:
        return await self._request("GET", "/info")

    async def pair(self, code: str, client_name: str = "Home Assistant") -> str:
        data = await self._request("POST", "/pair", {"code": code, "client_name": client_name})
        self._token = data["token"]
        return self._token

    async def status(self) -> dict[str, Any]:
        return await self._request("GET", "/status")

    async def pending_requests(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "/requests?status=pending")
        return data.get("items", []) if isinstance(data, dict) else []

    async def usage(self, start: str) -> list[dict[str, Any]]:
        data = await self._request("GET", f"/usage?from={start}")
        return data.get("items", []) if isinstance(data, dict) else []

    async def image(self, kind: str, item_id: str) -> bytes | None:
        """Game icon ("icons") or user avatar ("avatars") as JPEG, or None."""
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        try:
            async with asyncio.timeout(10):
                resp = await self._session.get(f"{self._base}/{kind}/{item_id}.jpg", headers=headers)
                if resp.status != 200:
                    return None
                return await resp.read()
        except (aiohttp.ClientError, TimeoutError):
            return None

    async def grant(self, profile_id: str, seconds: int, reason: str = "") -> None:
        await self._request("POST", f"/profiles/{profile_id}/grant", {"seconds": seconds, "reason": reason})

    async def approve(self, request_id: str, seconds: int | None = None) -> None:
        body = {"seconds": seconds} if seconds else {}
        await self._request("POST", f"/requests/{request_id}/approve", body)

    async def deny(self, request_id: str, message: str = "") -> None:
        await self._request("POST", f"/requests/{request_id}/deny", {"message": message})

    async def block(self, profile_id: str, minutes: int | None = None) -> None:
        body = {"minutes": minutes} if minutes else {}
        await self._request("POST", f"/profiles/{profile_id}/block", body)

    async def unblock(self, profile_id: str) -> None:
        await self._request("POST", f"/profiles/{profile_id}/unblock")

    async def set_locked(self, locked: bool) -> None:
        await self._request("POST", "/console/lock" if locked else "/console/unlock")
