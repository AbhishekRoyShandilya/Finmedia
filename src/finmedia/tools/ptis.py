"""Client for the PTIS research bridge (read-only HTTP on localhost). Every call passes `asof`; the bridge guarantees
nothing dated after it is used. Start the bridge from the PTIS repo:
    PTIS_ENV=test PYTHONPATH=. python -m research_bridge.server
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

BASE = os.environ.get("PTIS_BRIDGE_URL", "http://127.0.0.1:8010")


class BridgeError(RuntimeError):
    pass


class PtisBridge:
    def __init__(self, base: str = BASE, timeout: float = 300.0):
        self.base = base.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, **params: Any) -> Any:
        url = f"{self.base}{path}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:
            raise BridgeError(f"GET {path} failed: {exc}") from exc

    def _post(self, path: str, body: dict[str, Any]) -> Any:
        req = urllib.request.Request(f"{self.base}{path}", data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:
            raise BridgeError(f"POST {path} failed: {exc}") from exc

    def meta(self) -> dict:
        return self._get("/meta")

    def sector_map(self, asof: str) -> dict:
        return self._get("/sector_map", asof=asof)

    def macro_state(self, asof: str) -> dict:
        return self._get("/macro_state", asof=asof)

    def sector_state(self, sector: str, asof: str) -> dict:
        return self._get("/sector_state", sector=sector, asof=asof)

    def event_study(self, events: list[str], asof: str, sectors: list[str] | None = None,
                    horizons: tuple[int, ...] = (1, 5, 20, 60), condition: bool = True,
                    syms: list[str] | None = None) -> dict:
        return self._post("/event_study", dict(events=events, asof=asof, sectors=sectors or [], syms=syms or [],
                                               horizons=list(horizons), condition=condition))

    def beneficiaries(self, sector: str, events: list[str], asof: str, horizon: int = 20, top: int = 5) -> dict:
        return self._post("/beneficiaries", dict(sector=sector, events=events, asof=asof, horizon=horizon, top=top))
