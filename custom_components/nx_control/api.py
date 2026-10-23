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

        if resp.status in (401, 403):
            raise NXControlAuthError(await resp.text())
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

    async def grant(self, profile_id: str, seconds: int, reason: str = "") -> None:
        await self._request("POST", f"/profiles/{profile_id}/grant", {"seconds": seconds, "reason": reason})

    async def approve(self, request_id: str, seconds: int | None = None) -> None:
        body = {"seconds": seconds} if seconds else {}
        await self._request("POST", f"/requests/{request_id}/approve", body)

    async def deny(self, request_id: str, message: str = "") -> None:
        await self._request("POST", f"/requests/{request_id}/deny", {"message": message})

    async def set_locked(self, locked: bool) -> None:
        await self._request("POST", "/console/lock" if locked else "/console/unlock")
