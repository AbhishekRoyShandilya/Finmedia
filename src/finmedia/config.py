"""Load YAML configuration from the project's config/ and system/ folders."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    """Return the project root (FINMEDIA_ROOT, or the nearest folder with config/)."""
    env = os.environ.get("FINMEDIA_ROOT")
    if env:
        return Path(env).resolve()
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / "config" / "settings.yaml").exists():
            return candidate
    # Fall back to the repository layout this file ships in.
    return Path(__file__).resolve().parents[2]


def load_yaml(relative_path: str) -> dict[str, Any]:
    path = project_root() / relative_path
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=None)
def settings() -> dict[str, Any]:
    return load_yaml("config/settings.yaml")


def path_setting(key: str) -> Path:
    """Resolve a path from settings.pipeline relative to the project root."""
    return project_root() / settings()["pipeline"][key]
