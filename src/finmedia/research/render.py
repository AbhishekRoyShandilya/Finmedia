"""Render a research run: INTERNAL report (everything, watermarked) and a PUBLIC-SAFE draft built from structured
data only (facts, sector statistics, method, caveats - no persona text, no verdicts, no stock names), linted
against the advice-language rules. The public draft still needs human compliance review before publishing."""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from ..config import load_yaml

EDGE_PATHS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
PUBLIC_EXTRA_BANNED = ["overweight", "underweight", "accumulate", "buy ", "sell ", "top pick", "beneficiar",
                       "outperform", "underperform", "bullish", "bearish"]
HORIZONS = ["event day", "1 week", "1 month", "3 months"]

CSS = """
:root{--ink:#1d2330;--mut:#5b6474;--line:#dfe3ea;--bg:#fff;--pos:#137a3a;--neg:#b42318;--acc:#1f4fa3;--wm:rgba(180,35,24,.07)}
*{box-sizing:border-box}body{font:15px/1.55 -apple-system,Segoe UI,Inter,Roboto,sans-serif;color:var(--ink);
background:var(--bg);margin:0;padding:32px 16px}main{max-width:980px;margin:0 auto}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:34px 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}
h3{font-size:16px;margin:22px 0 8px}.meta{color:var(--mut);font-size:13px}.banner{padding:10px 14px;border-radius:6px;
margin:16px 0;font-size:13px}.int{background:#fdecea;color:var(--neg);border:1px solid #f5c2bd}
.pub{background:#eef3fb;color:var(--acc);border:1px solid #c9d7ef}table{border-collapse:collapse;width:100%;
font-size:13px;margin:6px 0 12px}th,td{border-bottom:1px solid var(--line);padding:5px 7px;text-align:right}
th:first-child,td:first-child{text-align:left}th{color:var(--mut);font-weight:600}.pos{color:var(--pos);font-weight:600}
.neg{color:var(--neg);font-weight:600}.card{border:1px solid var(--line);border-radius:8px;padding:12px 16px;margin:10px 0}
ul{margin:4px 0 8px 20px;padding:0}.small{font-size:12px;color:var(--mut)}.flag{color:var(--neg);font-weight:600}
body.internal::before{content:"INTERNAL — CONTAINS DIRECTIONAL VIEWS — NOT FOR DISTRIBUTION";position:fixed;top:45%;
left:-10%;width:120%;text-align:center;transform:rotate(-24deg);font-size:44px;font-weight:800;color:var(--wm);
pointer-events:none;z-index:0}main{position:relative;z-index:1}
.wrap{overflow-x:auto}
@media print{body{padding:0}h2{break-after:avoid}.card,table{break-inside:avoid}}
"""


def e(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def _ul(items: list[Any]) -> str:
    return "<ul>" + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>" if items else '<p class="small">none</p>'


def _dir(d: str) -> str:
    return f'<span class="{ {"positive": "pos", "negative": "neg"}.get(d, "")}">{e(d)}</span>'


def _hist_table(hist: dict[str, Any]) -> str:
    cols = ["n", "median", "q25", "q75", "hit_rate_pct", "t", "min", "max"]
    rows = "".join(f"<tr><td>{e(h)}</td>" + "".join(f"<td>{e(hist[h].get(c))}</td>" for c in cols) + "</tr>"
                   for h in HORIZONS if h in hist)
    if not rows:
        return '<p class="small">no analogue history</p>'
    return ('<div class="wrap"><table><tr><th>horizon</th>' + "".join(f"<th>{c}</th>" for c in cols) + "</tr>"
            + rows + "</table></div>")


def _similar_table(sim: dict[str, Any]) -> str:
    rows = ""
    for h in HORIZONS:
        for split, v in sim.get(h, {}).items():
            rows += (f"<tr><td>{e(h)}</td><td>{e(split)}</td><td>{e(v.get('n'))}</td><td>{e(v.get('median'))}</td>"
                     f"<td>{e(v.get('q25'))}</td><td>{e(v.get('q75'))}</td><td>{e(v.get('hit_rate_pct'))}</td></tr>")
    if not rows:
        return ""
    return ('<div class="wrap"><table><tr><th>horizon</th><th>regime like today</th><th>n</th><th>median</th>'
            "<th>q25</th><th>q75</th><th>hit %</th></tr>" + rows + "</table></div>")


LABELS = {"vol_60d_ann_pct": "volatility, 60-day annualised %", "drawdown_from_52w_high_pct": "below 52-week high %",
          "above_200dma": "above 200DMA", "breadth_above_50dma_pct": "members above 50DMA %", "n_members": "members",
          "india_vix": "India VIX", "vix_pct_rank_1y": "VIX percentile, 1 year", "nifty": "NIFTY 50",
          "nifty_vs_50dma_pct": "NIFTY vs 50DMA %", "nifty_vs_200dma_pct": "NIFTY vs 200DMA %",
          "nifty_ret_3m_pct": "NIFTY 3-month return %", "midcap100_vs_200dma_pct": "Midcap 100 vs 200DMA %"}


def _label(k: str) -> str:
    if k in LABELS:
        return LABELS[k]
    return k.replace("_chg_1m_pct", " 1-month change %").replace("_pct", " %").replace("_", " ")


def _state_table(state: dict[str, Any]) -> str:
    """Sector state: a returns grid (period x absolute / vs NIFTY) plus the remaining measures."""
    skip = {"asof", "sector", "caveat", "kind", "data_through"}
    periods = [p for p in ("1m", "3m", "6m", "12m") if f"ret_{p}_pct" in state]
    out = ""
    if periods:
        out += ('<div class="wrap"><table><tr><th>return %</th>' + "".join(f"<th>{p}</th>" for p in periods) + "</tr>"
                "<tr><td>absolute</td>" + "".join(f"<td>{e(state.get(f'ret_{p}_pct'))}</td>" for p in periods) + "</tr>"
                "<tr><td>vs NIFTY 50</td>" + "".join(f"<td>{e(state.get(f'rel_vs_nifty_{p}_pct'))}</td>" for p in periods)
                + "</tr></table></div>")
        skip |= {f"ret_{p}_pct" for p in periods} | {f"rel_vs_nifty_{p}_pct" for p in periods}
    rest = [(k, v) for k, v in state.items() if k not in skip and not k.endswith("_through")]
    if rest:
        out += ('<div class="wrap"><table><tr><th>measure</th><th>value</th></tr>'
                + "".join(f"<tr><td>{e(_label(k))}</td><td>{e(v)}</td></tr>" for k, v in rest) + "</table></div>")
    through = state.get("data_through") or state.get("macro_through")
    return out + (f'<p class="small">data through {e(through)}</p>' if through else "")


def _benef_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="small">no stock with 3+ analogue events</p>'
    cols = ["sym", "events_n", "avg_abn_pct", "median_abn_pct", "hit_rate_pct", "mom_6m_pct", "liquidity_rank"]
    return ('<div class="wrap"><table><tr>' + "".join(f"<th>{c}</th>" for c in cols) + "</tr>"
            + "".join("<tr>" + "".join(f"<td>{e(r.get(c))}</td>" for c in cols) + "</tr>" for r in rows)
            + "</table></div>")


def _facts(facts: list[dict[str, Any]]) -> str:
    if not facts:
        return '<p class="small">No primary document was provided; no event facts are cited.</p>'
    return "".join(f'<div class="card"><b>{e(f["claim"])}</b><div class="small">“{e(f["source_quote"])}” · '
                   f'sectors: {e(", ".join(f["sectors"]))}</div></div>' for f in facts)


def _page(title: str, body: str, internal: bool) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><title>{e(title)}</title><style>{CSS}</style></head>'
            f'<body class="{"internal" if internal else "public"}"><main>{body}</main></body></html>')


def internal_html(r: dict[str, Any]) -> str:
    cio, pack, ver = r["cio"], r["quant_pack"], r["verification"]
    flagged = [k for k, v in ver.items() if v.get("flagged")]
    b = [f"<h1>{e(cio['title'])}</h1>",
         f'<div class="meta">Topic: {e(r["topic"])} · Report date (asof): {e(r["asof"])} · Analogues: '
         f'{e(pack["analogues"]["set"])} (n {e(pack["analogues"]["n_events"])})</div>',
         '<div class="banner int"><b>INTERNAL.</b> Contains directional sector and stock views for the owner\'s own '
         "use. Not investment advice and not for distribution. Every number is taken from the PTIS quant pack or a "
         "quoted primary document and machine-checked.</div>"]
    if flagged:
        b.append(f'<div class="banner int flag">Verification flags: {e(", ".join(flagged))} — see the appendix.</div>')
    b += ["<h2>CIO summary</h2>", f"<p>{e(cio['summary'])}</p>", "<h2>Sector verdicts</h2>",
          '<div class="wrap"><table><tr><th>sector</th><th>direction</th><th>horizon</th><th>confidence</th>'
          "<th>expected range (history)</th></tr>"
          + "".join(f"<tr><td>{e(v['sector'])}</td><td>{_dir(v['direction'])}</td><td>{e(v['horizon'])}</td>"
                    f"<td>{e(v['confidence'])}</td><td>{e(v['expected_range'])}</td></tr>" for v in cio["sector_verdicts"])
          + "</table></div>"]
    for v in cio["sector_verdicts"]:
        sp = pack["sectors"].get(v["sector"], {})
        b += [f"<h3>{e(v['sector'])} — {_dir(v['direction'])}, {e(v['horizon'])}, {e(v['confidence'])} confidence</h3>",
              f"<p>{e(v['rationale'])}</p>",
              "<b>Stocks</b>" + _ul([f"{x['sym']}: {x['why']}" for x in v["top_beneficiaries"]]),
              "<b>What would change the view</b>" + _ul(v["what_would_change_view"]),
              "<b>Dates to watch</b>" + _ul(v["dates_to_watch"]),
              f"<b>State now</b> <span class='small'>({e(sp.get('state_now', {}).get('kind'))})</span>"
              + _state_table(sp.get("state_now", {})),
              "<b>After past analogues — abnormal return vs NIFTY, %</b>"
              + _hist_table(sp.get("history_abnormal_vs_nifty_pct", {}))
              + _similar_table(sp.get("history_in_similar_regime", {})),
              "<b>Stock history after analogues (1 month)</b>" + _benef_table(sp.get("beneficiaries_1m", []))]
    b += ["<h2>Disagreements</h2>", _ul(cio["disagreements"]), "<h2>Event facts (quoted)</h2>",
          (f'<p class="small">{e(r["fact_status_note"])}</p>' if r["facts"] else ""), _facts(r["facts"]), "<h2>Macro state now</h2>",
          _state_table(pack["macro_now"]), "<h2>Analyst panel</h2>"]
    for name, pv in r["personas"].items():
        b.append(f'<div class="card"><h3>{e(name.replace("_", " ").title())}: {e(pv["headline"])}</h3>'
                 + _ul(pv["key_points"])
                 + "<b>Sector views</b>" + _ul([f"{s['sector']}: {s['direction']}, {s['horizon']}, {s['confidence']} — "
                                                f"{s['rationale']}" for s in pv["sector_views"]])
                 + "<b>Actions / instruments</b>" + _ul(pv["instruments_or_actions"])
                 + "<b>Risks</b>" + _ul(pv["risks"]) + "</div>")
    sk = r["skeptic"]
    b += ["<h2>Skeptic review</h2>",
          _ul([f"[{c['severity']}] {c['target']}: {c['challenge']}" for c in sk["challenges"]]),
          "<b>Priced in?</b>" + _ul(sk["priced_in_notes"]), "<b>Data limits</b>" + _ul(sk["data_limits"]),
          "<h2>Caveats</h2>", _ul(cio["caveats"] + pack["caveats"]),
          "<h2>Appendix — verification</h2>",
          '<div class="wrap"><table><tr><th>step</th><th>numbers checked</th><th>attempts</th><th>unsupported</th></tr>'
          + "".join(f"<tr><td>{e(k)}</td><td>{e(v.get('checked'))}</td><td>{e(v.get('attempts'))}</td>"
                    f"<td class='{'flag' if v.get('flagged') else ''}'>{e(', '.join(v.get('unsupported', []) + v.get('beneficiaries_not_in_table', [])) or '—')}</td></tr>"
                    for k, v in ver.items()) + "</table></div>",
          f'<p class="small">Analogue events used: {e(", ".join(pack["analogues"]["events"]))}. '
          f'Facts dropped for a non-verbatim quote: {len(r.get("facts_dropped_bad_quote", []))}. '
          f'Sectors proposed by the scoper but not in the sector list: {e(", ".join(r.get("scoper_rejected_sectors", [])) or "none")}.</p>']
    return _page(cio["title"] + " — internal", "".join(b), internal=True)


def public_html(r: dict[str, Any]) -> str:
    """Structured data only. No persona text, no verdicts, no stock names, no directional language."""
    pack = r["quant_pack"]
    b = [f"<h1>{e(r['topic'])}: how sectors have behaved after past events</h1>",
         f'<div class="meta">Data as of {e(r["asof"])} · Analogues: {e(pack["analogues"]["set"])} '
         f'(n {e(pack["analogues"]["n_events"])})</div>',
         '<div class="banner pub">DRAFT for compliance review. Educational, historical statistics only. It is not '
         "investment advice and not a recommendation about any security. Past behaviour does not predict future returns.</div>",
         "<h2>What was announced</h2>", _facts(r["facts"]), "<h2>Sector statistics</h2>"]
    for s in r["sectors_studied"]:
        sp = pack["sectors"].get(s, {})
        b += [f"<h3>{e(s)}</h3>", "<b>Recent behaviour</b>" + _state_table(sp.get("state_now", {})),
              "<b>After past analogue events — return relative to NIFTY 50, %</b>"
              + _hist_table(sp.get("history_abnormal_vs_nifty_pct", {}))]
    b += ["<h2>Method and limits</h2>", _ul(pack["caveats"])]
    return _page(r["topic"] + " — sector statistics (draft)", "".join(b), internal=False)


def public_lint(text: str, result: dict[str, Any], rules: dict[str, Any] | None = None) -> list[str]:
    rules = rules or load_yaml("config/lint_rules.yaml")
    plain = re.sub(r"<[^>]+>", " ", text).lower()
    hits = [f"phrase:{p}" for p in rules.get("recommendation_phrases", []) + PUBLIC_EXTRA_BANNED if p.lower() in plain]
    syms = {row["sym"] for sp in result["quant_pack"]["sectors"].values() for row in sp.get("beneficiaries_1m", [])}
    syms |= {b["sym"] for v in result["cio"]["sector_verdicts"] for b in v["top_beneficiaries"]}
    words = set(re.findall(r"[a-z0-9&\-]+", plain))
    hits += [f"stock:{s}" for s in sorted(syms) if s.lower() in words]
    return hits


def to_pdf(html_path: Path) -> Path | None:
    edge = next((p for p in EDGE_PATHS if Path(p).exists()), None) or shutil.which("msedge")
    if not edge:
        return None
    pdf = html_path.with_suffix(".pdf")
    subprocess.run([edge, "--headless=new", "--disable-gpu", f"--print-to-pdf={pdf}", "--no-pdf-header-footer",
                    html_path.resolve().as_uri()], check=False, capture_output=True, timeout=120)
    for _ in range(40):            # Edge can return before the file is flushed when another instance is open
        if pdf.exists() and pdf.stat().st_size > 0:
            return pdf
        time.sleep(0.25)
    return None


def render_all(result: dict[str, Any], out_dir: Path, pdf: bool = True) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", result["topic"].lower()).strip("-")[:60] + "_" + result["asof"]
    internal = out_dir / f"{slug}_INTERNAL.html"
    public = out_dir / f"{slug}_public_draft.html"
    internal.write_text(internal_html(result), encoding="utf-8")
    pub_text = public_html(result)
    public.write_text(pub_text, encoding="utf-8")
    (out_dir / f"{slug}_run.json").write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str),
                                              encoding="utf-8")
    hits = public_lint(pub_text, result)
    result["public_lint"] = hits
    pdf_path = to_pdf(internal) if pdf else None
    return {"internal": str(internal), "internal_pdf": str(pdf_path) if pdf_path else None, "public": str(public),
            "public_lint_hits": hits}
