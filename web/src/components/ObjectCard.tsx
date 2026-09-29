import { useState } from "react";
import { api, withToken } from "../api";
import type { ContentItem, ResearchObject } from "../types";
import { DirPill, Err, VERDICT, go } from "../ui";

const KINDS: [string, string][] = [
  ["youtube", "YouTube script"],
  ["reel", "Reel / Short"],
  ["carousel", "Carousel"],
  ["newsletter", "Newsletter"],
];

export function ProvenanceBadge({ ro }: { ro: ResearchObject }) {
  const p = ro.provenance;
  if (!p) return null;
  return p.ok ? (
    <span className="pill pos" title="Every number traced to a tool result of the run">✓ {p.numbers_checked} numbers verified</span>
  ) : (
    <span className="pill neg" title="Provenance problems remained after one revision">
      ⚠ flagged: {p.unsupported_numbers.length} unsupported number(s), {p.bad_refs.length} bad ref(s)
    </span>
  );
}

export default function ObjectCard({ ro, compact = false, aiReady = true }: { ro: ResearchObject; compact?: boolean; aiReady?: boolean }) {
  const o = ro.object;
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");
  const [showAll, setShowAll] = useState(!compact);
  const verdict = VERDICT[o.verdict] || "";

  async function make(kind: string) {
    setBusy(kind);
    setErr("");
    try {
      const item = await api.post<ContentItem>(`/api/objects/${ro.key}/content`, { kind, version: ro.version });
      go(`content/${item.id}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="card" style={{ borderColor: "var(--accent)" }}>
      <div className="row between">
        <span className="eyebrow">Research Object · {ro.key} v{ro.version}</span>
        <div className="row">
          <ProvenanceBadge ro={ro} />
          <span className="pill">as of {ro.asof}</span>
          <span className="pill">{o.mode.replace(/_/g, " ")}</span>
        </div>
      </div>
      <h2>{o.title}</h2>
      {verdict && (
        <div className="banner info">
          <b>Verdict: {verdict}</b>
          {o.verdict_conditions ? <> — {o.verdict_conditions}</> : null}
        </div>
      )}
      <ul className="clean">{o.executive_summary.map((s, i) => <li key={i}>{s}</li>)}</ul>

      {o.claims.length > 0 && (
        <div className="wrap">
          <table className="t">
            <thead><tr><th>Claim</th><th>View</th><th>Horizon</th><th>Confidence</th><th>Why</th></tr></thead>
            <tbody>
              {o.claims.map((c, i) => (
                <tr key={i}>
                  <td className="mono">{c.target} {(c.direction === "positive" || c.direction === "negative") && <span className="mark" title="Directional: needs compliance sign-off before publishing">VIEW</span>}</td>
                  <td><DirPill d={c.direction} /></td>
                  <td>{c.horizon}</td>
                  <td>{c.confidence}</td>
                  <td className="small">{c.rationale} <span className="faint">{c.evidence_refs.join(" ")}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!showAll && (
        <button className="btn sm" onClick={() => setShowAll(true)} style={{ alignSelf: "flex-start" }}>
          Show full research ({o.sections.length} sections, {o.sources.length} sources)
        </button>
      )}
      {showAll && (
        <>
          {o.sections.map((s, i) => (
            <details key={i} open={!compact}>
              <summary><b>{s.heading}</b> <span className="faint tiny">{s.evidence_refs.join(" ")}</span></summary>
              <p style={{ whiteSpace: "pre-wrap", marginTop: 6 }}>{s.body}</p>
            </details>
          ))}
          {o.persona_views.length > 0 && (
            <div className="col">
              <h3>Analyst panel</h3>
              {o.persona_views.map((v, i) => (
                <div key={i} className="small"><b>{v.persona.replace(/_/g, " ")}:</b> {v.view}</div>
              ))}
            </div>
          )}
          <div className="grid2">
            <div className="col"><h3>Risks</h3><ul className="clean small">{o.risks.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
            <div className="col"><h3>What would change the view</h3><ul className="clean small">{o.what_would_change_view.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
            <div className="col"><h3>Data limits</h3><ul className="clean small">{o.data_limits.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
            {o.what_it_means_for_our_books && (
              <div className="col"><h3>Our books <span className="pill warn">internal</span></h3><p className="small">{o.what_it_means_for_our_books}</p></div>
            )}
          </div>
          <div className="col">
            <h3>Sources</h3>
            <ul className="clean small">
              {o.sources.map((s, i) => (
                <li key={i}>
                  {s.primary && <span className="pill acc">primary</span>} {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.title}</a> : s.title}
                  {s.published_at && <span className="faint"> · {s.published_at}</span>} <span className="faint">[{s.ref}]</span>
                </li>
              ))}
              {o.sources.length === 0 && <li className="faint">none cited</li>}
            </ul>
          </div>
          {(o.memory_updates.events.length + o.memory_updates.findings.length + o.memory_updates.structure_changes.length) > 0 && (
            <div className="small muted">
              Memory updates: {o.memory_updates.events.length} event(s), {o.memory_updates.findings.length} finding(s),{" "}
              {o.memory_updates.structure_changes.length} market-structure change(s).
            </div>
          )}
        </>
      )}

      <div className="row" style={{ borderTop: "1px solid var(--line)", paddingTop: 10 }}>
        <a className="btn sm" href={withToken(`/api/objects/${ro.key}/memo?version=${ro.version}`)} target="_blank" rel="noreferrer">Memo (internal)</a>
        <a className="btn sm" href={withToken(`/api/objects/${ro.key}/memo?version=${ro.version}&edition=public`)} target="_blank" rel="noreferrer">Memo (research edition)</a>
        {compact && <button className="btn sm" onClick={() => go(`object/${ro.key}/${ro.version}`)}>Open in library</button>}
        <span className="faint small">Make content:</span>
        {KINDS.map(([k, label]) => (
          <button key={k} className="btn sm" disabled={!!busy || !aiReady} onClick={() => make(k)}>
            {busy === k ? "Writing…" : label}
          </button>
        ))}
      </div>
      <Err msg={err} />
    </div>
  );
}
