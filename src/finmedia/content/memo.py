"""Render a Research Object as a standalone HTML memo (print to PDF from the browser, or headless Edge).

`internal=True` shows everything, watermarked. `internal=False` drops the internal section and memory updates;
directional claims stay, each MARKED for the compliance pass (the founder's rule: mark, never hide)."""

from __future__ import annotations

import html
from typing import Any

from ..research.render import CSS

VERDICT = {"works": "Works", "does_not_work": "Doesn't work", "works_only_when": "Works only when",
           "not_applicable": ""}


def e(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def _ul(items: list[Any]) -> str:
    return "<ul>" + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>" if items else '<p class="small">none</p>'


def render_memo(ro: dict[str, Any], internal: bool = True) -> str:
    o, p = ro["object"], ro.get("provenance", {})
    badge = ("numbers verified" if p.get("ok") else "FLAGGED: provenance problems remain") + \
        f" · {p.get('numbers_checked', 0)} numbers checked"
    verdict = VERDICT.get(o.get("verdict", ""), "")
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
             f"<title>{e(o['title'])}</title><style>{CSS}.mark{{background:#fff4d6;border:1px solid #e7c46a;border-radius:4px;"
             f"padding:0 5px;font-size:11px;font-weight:700;color:#8a5a00;margin-left:6px}}</style></head>"
             f"<body class='{'internal' if internal else ''}'><main>",
             f"<h1>{e(o['title'])}</h1><div class='meta'>{e(ro['key'])} v{e(ro['version'])} · as of {e(ro['asof'])} · "
             f"{e(o.get('mode'))} · {e(badge)}</div>",
             "<div class='banner int'>INTERNAL — contains directional views and the firm's own notes.</div>" if internal else
             "<div class='banner pub'>Research edition. Items marked VIEW are directional and need compliance sign-off before publishing.</div>",
             f"<p><b>Question.</b> {e(o['question'])}</p>",
             "<h2>Summary</h2>" + _ul(o.get("executive_summary", []))]
    if verdict:
        parts.append(f"<div class='card'><b>Verdict: {e(verdict)}</b>"
                     + (f"<br>{e(o.get('verdict_conditions'))}" if o.get("verdict_conditions") else "") + "</div>")
    for s in o.get("sections", []):
        parts.append(f"<h2>{e(s['heading'])}</h2><p>{e(s['body']).replace(chr(10), '<br>')}</p>"
                     f"<p class='small'>evidence: {e(', '.join(s.get('evidence_refs', [])))}</p>")
    if o.get("claims"):
        rows = "".join(
            f"<tr><td>{e(c['target'])}{'<span class=mark>VIEW</span>' if c['direction'] in ('positive', 'negative') else ''}</td>"
            f"<td class='{ {'positive': 'pos', 'negative': 'neg'}.get(c['direction'], '')}'>{e(c['direction'])}</td>"
            f"<td>{e(c['horizon'])}</td><td>{e(c['confidence'])}</td><td style='text-align:left'>{e(c['rationale'])}</td></tr>"
            for c in o["claims"])
        parts.append("<h2>Claims (scored later against what happened)</h2><div class='wrap'><table><tr><th>target</th>"
                     "<th>direction</th><th>horizon</th><th>confidence</th><th>rationale</th></tr>" + rows + "</table></div>")
    if o.get("persona_views"):
        parts.append("<h2>Analyst panel</h2>" + "".join(f"<div class='card'><b>{e(v['persona'])}</b><br>{e(v['view'])}</div>"
                                                         for v in o["persona_views"]))
    parts += ["<h2>Risks</h2>" + _ul(o.get("risks", [])),
              "<h2>What would change the view</h2>" + _ul(o.get("what_would_change_view", [])),
              "<h2>Data limits</h2>" + _ul(o.get("data_limits", []))]
    if internal and o.get("what_it_means_for_our_books"):
        parts.append(f"<h2>What it means for our books (internal)</h2><p>{e(o['what_it_means_for_our_books'])}</p>")
    def source_li(s: dict[str, Any]) -> str:
        bits = [("<b>primary</b> · " if s.get("primary") else "") + e(s["title"])]
        if s.get("published_at"):
            bits.append(e(s["published_at"]))
        if s.get("url"):
            bits.append(f'<a href="{e(s["url"])}">link</a>')
        return f"<li>{' · '.join(bits)} <span class='small'>[{e(s['ref'])}]</span></li>"

    src = "".join(source_li(s) for s in o.get("sources", []))
    parts.append("<h2>Sources</h2><ul>" + (src or "<li>none</li>") + "</ul>")
    if internal and p:
        issues = p.get("unsupported_numbers") or []
        parts.append("<h2>Provenance</h2><p class='small'>"
                     f"{e(p.get('numbers_checked'))} numbers checked; unsupported: {e(len(issues))}; "
                     f"bad refs: {e(p.get('bad_refs'))}; unfetched sources: {e(p.get('unfetched_sources'))}</p>")
        idx = p.get("evidence_index") or {}
        if idx:
            parts.append("<details><summary class='small'>Evidence log</summary><ul class='small'>" + "".join(
                f"<li>{e(r)} {e(v.get('tool'))} {e(str(v.get('args'))[:160])} {'' if v.get('ok') else '(failed)'}</li>"
                for r, v in idx.items()) + "</ul></details>")
    parts.append("</main></body></html>")
    return "".join(parts)
