import { api } from "../api";
import type { ResearchObject, Status } from "../types";
import { DirPill, Err, fmtTime, go, useAsync } from "../ui";
import ObjectCard from "../components/ObjectCard";

export default function ObjectPage({ objKey, version, status }: { objKey?: string; version?: string; status: Status | null }) {
  const { data: ro, error } = useAsync(
    () => api.get<ResearchObject>(`/api/objects/${objKey}${version ? `?version=${version}` : ""}`),
    [objKey, version],
  );
  if (!objKey) return <div className="page"><Err msg="No object selected" /></div>;

  return (
    <div className="page">
      <div className="row between">
        <button className="btn sm" onClick={() => go("library")}>← Library</button>
        {ro && (
          <div className="row">
            <span className="small muted">Version</span>
            {ro.versions.map((v) => (
              <button key={v} className={`btn sm ${v === ro.version ? "pri" : ""}`} onClick={() => go(`object/${ro.key}/${v}`)}>v{v}</button>
            ))}
            {ro.thread_id && <button className="btn sm" onClick={() => go(`research/${ro.thread_id}`)}>Open conversation</button>}
          </div>
        )}
      </div>
      <Err msg={error} />
      {ro && (
        <>
          {ro.status === "flagged" && (
            <div className="banner bad">
              This version is FLAGGED: after one revision it still had {ro.provenance.unsupported_numbers.length} number(s) not found in the evidence
              {ro.provenance.unsupported_numbers.length > 0 && <> ({ro.provenance.unsupported_numbers.map((u) => u.number).join(", ")})</>}. Treat those numbers as unverified.
            </div>
          )}
          <ObjectCard ro={ro} aiReady={!!status?.ai.ready} />

          <div className="card">
            <h3>Content built from this object</h3>
            {ro.content && ro.content.length > 0 ? (
              <table className="t">
                <thead><tr><th>Kind</th><th>Title</th><th>Built on</th><th>Status</th><th>Updated</th></tr></thead>
                <tbody>
                  {ro.content.map((c) => (
                    <tr key={c.id} style={{ cursor: "pointer" }} onClick={() => go(`content/${c.id}`)}>
                      <td>{c.kind}</td><td>{c.title}</td><td>v{c.object_version}</td>
                      <td><span className={`pill ${c.status === "approved" || c.status === "published" ? "pos" : c.status === "stale" ? "warn" : ""}`}>{c.status}</span></td>
                      <td className="small">{fmtTime(c.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p className="small muted">None yet. Use the “Make content” buttons above.</p>}
          </div>

          <div className="card">
            <h3>Claims ledger for this version</h3>
            <p className="small muted">Scored automatically after each horizon passes (needs the PTIS bridge for sector and stock claims).</p>
            <table className="t">
              <thead><tr><th>Target</th><th>View</th><th>Horizon</th><th>Confidence</th><th>Outcome</th></tr></thead>
              <tbody>
                {ro.claims_rows?.map((c) => {
                  const o = c.outcome_json ? JSON.parse(String(c.outcome_json)) : null;
                  return (
                    <tr key={c.id}>
                      <td className="mono">{c.target}</td><td><DirPill d={c.direction} /></td><td>{c.horizon}</td><td>{c.confidence}</td>
                      <td className="small">{o ? `${o.abnormal_pct}% vs NIFTY · ${o.hit === null ? "n/a" : o.hit ? "hit" : "miss"}` : "pending"}</td>
                    </tr>
                  );
                })}
                {(!ro.claims_rows || ro.claims_rows.length === 0) && <tr><td colSpan={5} className="muted small">No directional claims.</td></tr>}
              </tbody>
            </table>
          </div>

          {ro.provenance.evidence_index && (
            <details className="card">
              <summary><b>Evidence log</b> <span className="small muted">({Object.keys(ro.provenance.evidence_index).length} tool calls)</span></summary>
              <table className="t">
                <tbody>
                  {Object.entries(ro.provenance.evidence_index).map(([ref, e]) => (
                    <tr key={ref}><td className="mono">{ref}</td><td className="mono">{e.tool}</td><td className="small mono">{JSON.stringify(e.args).slice(0, 160)}</td><td>{e.ok ? "✓" : "failed"}</td></tr>
                  ))}
                </tbody>
              </table>
            </details>
          )}
        </>
      )}
    </div>
  );
}
