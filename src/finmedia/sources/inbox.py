"""Local inbox: official documents saved by hand (PDF, .txt, .md).

Phase 0 is manual-first: when a feed can't reach a source, download the
circular or filing and drop it in data/inbox/. The first non-empty line of a
text file is used as its title; an optional `URL: ...` line records the
original link.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from ..models import Document

SUPPORTED = {".pdf", ".txt", ".md"}


def _read_pdf(path: Path) -> str:
    from pypdf import PdfReader  # imported lazily; only needed for PDFs

    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        pages.append(f"[page {i}]\n{page.extract_text() or ''}")
    return "\n".join(pages)


def read_file(path: Path, source: dict[str, Any]) -> Document:
    if path.suffix.lower() == ".pdf":
        text = _read_pdf(path)
        title = path.stem.replace("_", " ")
        url = ""
    else:
        raw = path.read_text(encoding="utf-8")
        lines = [ln.strip() for ln in raw.splitlines()]
        title = next((ln.lstrip("# ") for ln in lines if ln), path.stem)
        url = next((ln.split(":", 1)[1].strip() for ln in lines if ln.lower().startswith("url:")), "")
        text = raw
    return Document(
        source_id=source.get("id", "inbox"),
        title=title,
        url=url or path.resolve().as_uri(),
        text=text,
        published_at=datetime.fromtimestamp(path.stat().st_mtime),
        category=source.get("category", "manual"),
    )


def read_inbox(inbox_dir: Path | str | None, source: dict[str, Any]) -> list[Document]:
    folder = Path(inbox_dir) if inbox_dir else None
    if not folder or not folder.exists():
        return []
    return [read_file(p, source) for p in sorted(folder.iterdir()) if p.suffix.lower() in SUPPORTED]
