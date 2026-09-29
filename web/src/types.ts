export type Direction = "positive" | "negative" | "neutral" | "mixed";

export interface Claim {
  target: string;
  direction: Direction;
  horizon: string;
  confidence: string;
  rationale: string;
  evidence_refs: string[];
}

export interface SourceRef {
  ref: string;
  title: string;
  url: string;
  published_at: string;
  primary: boolean;
}

export interface ResearchObjectBody {
  title: string;
  question: string;
  mode: string;
  executive_summary: string[];
  verdict: string;
  verdict_conditions: string;
  sections: { heading: string; body: string; evidence_refs: string[] }[];
  claims: Claim[];
  persona_views: { persona: string; view: string }[];
  risks: string[];
  what_would_change_view: string[];
  data_limits: string[];
  sources: SourceRef[];
  what_it_means_for_our_books: string;
  memory_updates: {
    events: { title: string; event_date: string; stage: string; mechanism_tags: string[]; summary: string }[];
    findings: { statement: string; status: string; tags: string[] }[];
    structure_changes: { title: string; effective_date: string; description: string; affects: string[] }[];
  };
}

export interface Provenance {
  ok: boolean;
  numbers_checked: number;
  unsupported_numbers: { number: string; where: string; text: string }[];
  bad_refs: string[];
  unfetched_sources: string[];
  directional_claims: number;
  stock_level_claims: number;
  attempts?: number;
  evidence_index?: Record<string, { tool: string; args: unknown; ok: boolean; at?: string }>;
}

export interface ResearchObject {
  id: number;
  key: string;
  version: number;
  thread_id: number | null;
  run_id: number | null;
  title: string;
  asof: string;
  created_at: string;
  status: string;
  object: ResearchObjectBody;
  provenance: Provenance;
  versions: number[];
  claims_rows?: ClaimRow[];
  content?: ContentItem[];
}

export interface ObjectListItem {
  key: string;
  version: number;
  title: string;
  asof: string;
  created_at: string;
  status: string;
  mode: string;
  verdict: string;
  n_claims: number;
  summary: string;
  thread_id: number | null;
}

export interface RunEvent {
  seq: number;
  ts: string;
  type: string;
  data: Record<string, any>;
}

export interface RunInfo {
  id: number;
  kind: string;
  question: string;
  status: string;
  depth: string | null;
  asof: string | null;
  started_at: string;
  finished_at: string | null;
  cost_inr: number;
  error: string | null;
  active: boolean;
  result: any;
}

export interface Thread {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  asof: string | null;
  object_key: string | null;
  last_status?: string;
  cost_inr?: number;
  n_runs?: number;
  runs?: RunInfo[];
  object?: ResearchObject | null;
}

export interface Lint {
  passed: boolean;
  errors: string[];
  warnings: string[];
  compliance_items: string[];
  needs_signoff: boolean;
  cost_inr?: number;
}

export interface ContentItem {
  id: number;
  object_key: string;
  object_version: number;
  kind: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
  draft?: any;
  lint: Lint;
  approvals: { name: string; role: string; note: string; at: string }[];
}

export interface MemoryRecord {
  id: number;
  kind: string;
  title: string;
  body: string;
  data: any;
  tags: string[];
  entities: string[];
  event_date: string | null;
  known_at: string;
  status: string;
  source_ref: string;
  supersedes: number | null;
  created_by: string;
}

export interface DocumentRow {
  id: number;
  source_id: string;
  title: string;
  url: string;
  category: string;
  published_at: string | null;
  fetched_at: string;
  symbol: string | null;
  doc_type: string | null;
  snippet: string;
}

export interface SourceStatus {
  id: string;
  type: string;
  category: string;
  enabled: boolean;
  interval_min: number;
  url: string | null;
  documents: number;
  last_run: string | null;
  last_ok: string | null;
  last_error: string | null;
  fail_streak: number;
  last_new: number;
  next_due: string | null;
}

export interface ClaimRow {
  id: number;
  run_id: number;
  asof: string;
  target: string;
  direction: Direction;
  horizon: string;
  confidence: string;
  source: string;
  object_key: string | null;
  object_version: number | null;
  rationale: string | null;
  directional: number;
  outcome_json?: string | null;
  outcome?:{ scored_on: string; abnormal_pct: number; hit: boolean | null } | null;
}

export interface Status {
  ai: { provider: string; ready: boolean; key: string | null; models: Record<string, string>; note: string };
  keys: { key: string; present: boolean; unlocks: string }[];
  bridge: { url: string; reachable: boolean };
  web_search: string | null;
  budget: Record<string, number | string>;
  collectors: { enabled: boolean; running: boolean; last_tick: string | null };
  memory: Record<string, number>;
  depths: Record<string, { max_steps: number; budget_inr: number }>;
  today: string;
}
