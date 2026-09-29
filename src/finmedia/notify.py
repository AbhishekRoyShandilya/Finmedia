"""Optional Telegram alerts (collector failures, finished research). Silent no-op without keys; never raises."""

from __future__ import annotations

import httpx

from .env import get_key


def configured() -> bool:
    return bool(get_key("TELEGRAM_BOT_TOKEN") and get_key("TELEGRAM_CHAT_ID"))


def send(text: str) -> bool:
    if not configured():
        return False
    try:
        r = httpx.post(f"https://api.telegram.org/bot{get_key('TELEGRAM_BOT_TOKEN')}/sendMessage",
                       json={"chat_id": get_key("TELEGRAM_CHAT_ID"), "text": text[:3900]}, timeout=15)
        return r.status_code == 200
    except Exception:  # noqa: BLE001 - alerts must never break the app
        return False
