"""Step 3 - the QUANT PACK: every number the analysts may use, fetched deterministically from the PTIS bridge.
Values are rounded to 2 decimals so the analysts quote exactly what the verifier can check."""

from __future__ import annotations

from typing import Any

from ..tools.ptis import PtisBridge
from .cases import analogue_dates

HORIZONS = (1, 5, 20, 60)
HORIZON_NAMES = {"1": "event day", "5": "1 week", "20": "1 month", "60": "3 months"}


def _r(x: Any) -> Any:
    if isinstance(x, float):
        return round(x, 2) + 0.0          # + 0.0 turns -0.0 into 0.0
    if isinstance(x, dict):
        return {k: _r(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_r(v) for v in x]
    return x


def build_pack(bridge: PtisBridge, sectors: list[str], analogue_set: str, asof: str) -> dict[str, Any]:
    events = analogue_dates(analogue_set, asof)
    macro = bridge.macro_state(asof)
    regime = {"vix_high": (macro.get("vix_pct_rank_1y") or 0) >= 50,
              "nifty_above_200dma": (macro.get("nifty_vs_200dma_pct") or 0) > 0}
    pack: dict[str, Any] = {
        "asof": asof,
        "macro_now": _r(macro),
        "regime_now": regime,
        "analogues": {"set": analogue_set, "n_events": len(events), "events": events},
        "horizon_names": HORIZON_NAMES,
        "sectors": {},
        "caveats": [
            "Abnormal = sector (or stock) return minus NIFTY 50, measured from the close BEFORE the event.",
            "Horizons are trading sessions: 1 = event day, 5 = about a week, 20 = about a month, 60 = about three months.",
            "Sector membership uses today's NSE sector labels; baskets before ~2016 lean toward survivors.",
            "History describes what happened after past budgets; it is not a forecast, and small n means wide uncertainty.",
        ],
    }
    es = bridge.event_study(events, asof, sectors=sectors, horizons=HORIZONS, condition=True) if events else {"targets": {}}
    measured = sorted({r["event"] for t in es["targets"].values() for r in t.get("per_event", [])
                       if r.get("abn") is not None})
    unmeasured = [e for e in events if e not in measured]
    pack["analogues"] = {"set": analogue_set, "n_listed": len(events), "n_events": len(measured), "events": measured,
                         "not_measured": unmeasured}
    if unmeasured:
        pack["caveats"].append(
            f"{len(unmeasured)} earlier analogue events ({unmeasured[0]} to {unmeasured[-1]}) are not measured: the "
            "NIFTY 50 benchmark series starts in September 2007, and pre-2008 sector baskets would be survivor-heavy.")
    for s in sectors:
        entry: dict[str, Any] = {"state_now": _r(bridge.sector_state(s, asof))}
        t = es["targets"].get(f"sector:{s}", {})
        hist, similar = {}, {}
        for h, summ in t.get("summary", {}).items():
            core = {k: summ.get(k) for k in ("n", "median", "mean", "q25", "q75", "hit_rate_pct", "t", "min", "max")}
            hist[HORIZON_NAMES.get(h, h)] = _r(core)
            for fk, val in regime.items():
                sub = summ.get(f"{fk}={val}", {})
                if sub.get("n"):
                    similar.setdefault(HORIZON_NAMES.get(h, h), {})[f"{fk}={val}"] = _r(
                        {k: sub.get(k) for k in ("n", "median", "q25", "q75", "hit_rate_pct")})
        entry["history_abnormal_vs_nifty_pct"] = hist
        entry["history_in_similar_regime"] = similar
        entry["history_kind"] = t.get("kind")
        if events:
            b = bridge.beneficiaries(s, events, asof, horizon=20, top=5)
            entry["beneficiaries_1m"] = _r(b.get("ranked", []))
            entry["beneficiaries_method"] = b.get("method")
        pack["sectors"][s] = entry
    return pack
