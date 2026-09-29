"""Background collectors: fetch every enabled source on its interval, store new documents (append-only; the time we
first saw an item is its known_at), track health, alert on repeated failures, and score due claims once a day.

Runs inside the web server (a daemon thread) or once from the CLI: `finmedia collect`.
"""

from __future__ import annotations

import threading
import time
from datetime import date, datetime, timedelta
from typing import Any

from . import notify
from .config import load_yaml, path_setting
from .sources import NSE_TYPES, fetch_source, nse_documents
from .store import Store, now


def sources() -> list[dict[str, Any]]:
    return load_yaml("config/sources.yaml")["sources"]


def run_source(store: Store, source: dict[str, Any], alert_after: int = 3) -> dict[str, Any]:
    sid = source["id"]
    started = now()
    try:
        if source["type"] in NSE_TYPES:
            pairs = nse_documents(source)
        else:
            pairs = [(d, {}) for d in fetch_source(source, inbox_dir=path_setting("inbox_dir"))]
        new = sum(store.add_document(d, symbol=m.get("symbol"), doc_type=m.get("doc_type")) is not None
                  for d, m in pairs)
        store.ex("""INSERT INTO collector_state (source_id, last_run, last_ok, last_error, fail_streak, fetched_total,
                    new_total, last_new) VALUES (?, ?, ?, NULL, 0, ?, ?, ?)
                    ON CONFLICT(source_id) DO UPDATE SET last_run = excluded.last_run, last_ok = excluded.last_ok,
                    last_error = NULL, fail_streak = 0, fetched_total = fetched_total + excluded.fetched_total,
                    new_total = new_total + excluded.new_total, last_new = excluded.last_new""",
                 (sid, started, started, len(pairs), new, new))
        return {"source": sid, "ok": True, "fetched": len(pairs), "new": new}
    except Exception as exc:  # noqa: BLE001 - one broken source must not stop the others
        err = f"{type(exc).__name__}: {exc}"[:500]
        store.ex("""INSERT INTO collector_state (source_id, last_run, last_error, fail_streak) VALUES (?, ?, ?, 1)
                    ON CONFLICT(source_id) DO UPDATE SET last_run = excluded.last_run, last_error = excluded.last_error,
                    fail_streak = fail_streak + 1""", (sid, started, err))
        streak = store.q1("SELECT fail_streak FROM collector_state WHERE source_id = ?", (sid,))["fail_streak"]
        if streak == alert_after:
            notify.send(f"Finmedia collector '{sid}' failed {streak} times in a row: {err}")
        return {"source": sid, "ok": False, "error": err}


def status(store: Store) -> list[dict[str, Any]]:
    state = {r["source_id"]: dict(r) for r in store.q("SELECT * FROM collector_state")}
    counts = {r["source_id"]: r["n"] for r in store.q("SELECT source_id, COUNT(*) AS n FROM documents GROUP BY source_id")}
    out = []
    for s in sources():
        st = state.get(s["id"], {})
        interval = int(s.get("interval_min") or 60)
        due = None
        if st.get("last_run"):
            due = (datetime.fromisoformat(st["last_run"]) + timedelta(minutes=interval)).isoformat(timespec="seconds")
        out.append({"id": s["id"], "type": s["type"], "category": s.get("category"), "enabled": bool(s.get("enabled", True)),
                    "interval_min": interval, "url": s.get("url"), "documents": counts.get(s["id"], 0),
                    "last_run": st.get("last_run"), "last_ok": st.get("last_ok"), "last_error": st.get("last_error"),
                    "fail_streak": st.get("fail_streak", 0), "last_new": st.get("last_new", 0), "next_due": due})
    return out


def run_due(store: Store, alert_after: int = 3, force: bool = False) -> list[dict[str, Any]]:
    results = []
    stat = {s["id"]: s for s in status(store)}
    for s in sources():
        if not s.get("enabled", True):
            continue
        st = stat[s["id"]]
        if force or not st["next_due"] or st["next_due"] <= now():
            results.append(run_source(store, s, alert_after))
    return results


def score_due_claims(store: Store) -> dict[str, Any]:
    from .research.pipeline import score_claims
    from .tools.ptis import PtisBridge

    bridge = PtisBridge(timeout=120)
    if not PtisBridge(base=bridge.base, timeout=3).reachable():
        return {"skipped": "PTIS bridge not running"}
    res = score_claims(store, bridge, date.today().isoformat())
    store.set_state("last_postmortem", date.today().isoformat())
    return res


class Scheduler:
    """Daemon loop: every minute run due collectors; once a day (after postmortem_hour) score due claims."""

    def __init__(self, store: Store, cfg: dict[str, Any]):
        self.store = store
        self.cfg = cfg.get("collectors", {})
        self._stop = threading.Event()
        self.thread: threading.Thread | None = None
        self.last_tick: str | None = None
        self.last_results: list[dict[str, Any]] = []

    def start(self) -> None:
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name="collectors", daemon=True)
            self.thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.last_results = run_due(self.store, int(self.cfg.get("alert_after_failures", 3))) or self.last_results
                hour = int(self.cfg.get("postmortem_hour", 18))
                if datetime.now().hour >= hour and self.store.get_state("last_postmortem") != date.today().isoformat():
                    score_due_claims(self.store)
                    self.store.set_state("last_postmortem", date.today().isoformat())
            except Exception as exc:  # noqa: BLE001
                notify.send(f"Finmedia scheduler error: {exc}")
            self.last_tick = now()
            self._stop.wait(60)
