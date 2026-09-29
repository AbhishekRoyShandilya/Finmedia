"""Load secrets from a `.env` file in the project root (git-ignored), without overriding real environment variables.

Only KEY=VALUE lines are read; quotes around the value are stripped. Nothing here is ever logged or returned by the
API: `keys_status()` reports only whether each key is present.
"""

from __future__ import annotations

import os

from .config import project_root

# Every external credential the system can use, and what it unlocks. Missing keys disable that feature only.
KNOWN_KEYS: dict[str, str] = {
    "ANTHROPIC_API_KEY": "Claude models (lead researcher, analyst panel, content). Needed when agent.provider = anthropic",
    "OPENAI_COMPAT_API_KEY": "Any OpenAI-compatible provider (Groq, OpenAI, OpenRouter, Together...). Needed when agent.provider = openai_compat",
    "FRED_API_KEY": "US macro series from FRED (Fed funds, yields, CPI, payrolls). Free key at fred.stlouisfed.org",
    "TAVILY_API_KEY": "Web search for the researcher (one of Tavily / Brave / SerpAPI is enough)",
    "BRAVE_SEARCH_API_KEY": "Web search via Brave Search API",
    "SERPAPI_API_KEY": "Web search via SerpAPI (Google results)",
    "TELEGRAM_BOT_TOKEN": "Alerts when a collector keeps failing or a research run finishes (with TELEGRAM_CHAT_ID)",
    "TELEGRAM_CHAT_ID": "Chat that receives the Telegram alerts",
    "FINMEDIA_APP_TOKEN": "Optional password for the web app (required if the server is reachable by others)",
}

_loaded = False


def load_env() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    path = project_root() / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def get_key(name: str) -> str | None:
    load_env()
    value = os.environ.get(name, "").strip()
    return value or None


def keys_status() -> list[dict[str, object]]:
    load_env()
    return [{"key": k, "present": bool(os.environ.get(k, "").strip()), "unlocks": v} for k, v in KNOWN_KEYS.items()]
