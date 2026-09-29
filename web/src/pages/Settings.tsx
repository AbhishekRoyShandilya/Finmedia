import { useState } from "react";
import { api, getToken, setToken } from "../api";
import type { Status } from "../types";
import { inr, useAsync } from "../ui";

interface ToolInfo { name: string; group: string; description: string; available: boolean; why: string | null }

export default function Settings({ status }: { status: Status | null }) {
  const tools = useAsync(() => api.get<ToolInfo[]>("/api/tools"), []);
  const costs = useAsync(() => api.get<any>("/api/costs"), []);
  const [tok, setTok] = useState(getToken());
  const [saved, setSaved] = useState(false);
  const b = status?.budget;

  return (
    <div className="page">
      <div><span className="eyebrow">Settings</span><h1>Keys, providers, budget and tools</h1></div>

      <div className="card">
        <h3>How to add keys</h3>
        <p className="small">Create a file named <span className="mono">.env</span> in the Finmedia folder (next to <span className="mono">pyproject.toml</span>) with one <span className="mono">KEY=value</span> per line, then restart <span className="mono">finmedia serve</span>. A template is in <span className="mono">.env.example</span>. Keys never leave the server and are never shown here, only whether they are present.</p>
        <p className="small">Choose the LLM in <span className="mono">config/settings.yaml → agent.provider</span>: <b>anthropic</b> (Claude), <b>openai_compat</b> (Groq, OpenAI, OpenRouter, Together or a local Ollama: set <span className="mono">base_url</span> and models), or <b>demo</b> (no key; scripted walk-through to test the app).</p>
      </div>

      {status && (
        <div className="grid2">
          <div className="card">
            <h3>LLM provider</h3>
            <div className="row"><span className={`dot ${status.ai.ready ? "ok" : "bad"}`} /> <b>{status.ai.provider}</b> {status.ai.ready ? "ready" : "not configured"}</div>
            {status.ai.note && <div className="small muted">{status.ai.note}</div>}
            <table className="t"><tbody>{Object.entries(status.ai.models).map(([r, m]) => <tr key={r}><td>{r}</td><td className="mono">{m}</td></tr>)}</tbody></table>
          </div>
          <div className="card">
            <h3>Services</h3>
            <div className="row small"><span className={`dot ${status.bridge.reachable ? "ok" : ""}`} /> PTIS quant bridge ({status.bridge.url}): {status.bridge.reachable ? "online" : "offline"}</div>
            {!status.bridge.reachable && <div className="tiny faint mono">In the PTIS repo: set PTIS_ENV=test and run python -m research_bridge.server</div>}
            <div className="row small"><span className={`dot ${status.web_search ? "ok" : ""}`} /> Web search: {status.web_search || "not configured"}</div>
            <div className="row small"><span className={`dot ${status.collectors.running ? "ok" : ""}`} /> Collectors: {status.collectors.running ? `running (last check ${status.collectors.last_tick || "—"})` : "off"}</div>
          </div>
        </div>
      )}

      {status && (
        <div className="card">
          <h3>API keys</h3>
          <table className="t">
            <thead><tr><th>Key</th><th>Status</th><th>Unlocks</th></tr></thead>
            <tbody>
              {status.keys.map((k) => (
                <tr key={k.key}><td className="mono">{k.key}</td><td>{k.present ? <span className="pill pos">present</span> : <span className="pill">missing</span>}</td><td className="small">{k.unlocks}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {b && (
        <div className="card">
          <h3>Budget ({b.month})</h3>
          <div className="grid4">
            <div className="stat"><span className="small muted">Research spent / cap</span><b>{inr(Number(b.research_spent_inr))} / {inr(Number(b.research_cap_inr))}</b></div>
            <div className="stat"><span className="small muted">Research left</span><b>{inr(Number(b.research_left_inr))}</b></div>
            <div className="stat"><span className="small muted">Content (media) LLM</span><b>{inr(Number(b.media_llm_spent_inr))} / {inr(Number(b.media_llm_cap_inr))}</b></div>
            <div className="stat"><span className="small muted">All spend / monthly cap</span><b>{inr(Number(b.total_spent_inr))} / {inr(Number(b.monthly_cap_inr))}</b></div>
          </div>
          <p className="tiny faint">Caps are in config/settings.yaml (budget). Every call is checked against the worst case before it runs. The research cap of ₹12,000 is a placeholder until you confirm it.</p>
          {costs.data?.rows?.length > 0 && (
            <table className="t">
              <thead><tr><th>Pool</th><th>Item</th><th>Calls</th><th>₹</th></tr></thead>
              <tbody>{costs.data.rows.map((r: any, i: number) => <tr key={i}><td>{r.kind}</td><td className="mono small">{r.item}</td><td>{r.calls}</td><td>{inr(r.inr)}</td></tr>)}</tbody>
            </table>
          )}
        </div>
      )}

      <div className="card">
        <h3>Research tools</h3>
        <table className="t">
          <thead><tr><th>Tool</th><th>Group</th><th>Available</th><th>What it does</th></tr></thead>
          <tbody>
            {tools.data?.map((t) => (
              <tr key={t.name}><td className="mono">{t.name}</td><td className="small">{t.group}</td>
                <td>{t.available ? <span className="pill pos">yes</span> : <span className="pill" title={t.why || ""}>{t.why}</span>}</td>
                <td className="small">{t.description}</td></tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>App token (this browser)</h3>
        <p className="small muted">Only needed if the server has FINMEDIA_APP_TOKEN set.</p>
        <div className="row">
          <input type="password" value={tok} onChange={(e) => { setTok(e.target.value); setSaved(false); }} placeholder="token" />
          <button className="btn" onClick={() => { setToken(tok); setSaved(true); }}>Save</button>
          {saved && <span className="small" style={{ color: "var(--pos)" }}>Saved. Reload the page.</span>}
        </div>
      </div>
    </div>
  );
}
