# Finmedia

A research desk and content engine for evidence-based Indian market research. You ask an open question in a chat
workspace; an AI lead researcher plans, pulls primary sources, checks the firm's research memory and measured market
history, consults an analyst panel, red-teams itself, and delivers **one verified Research Object**. Every number in
it is traced to a source it fetched. Content (YouTube scripts, Reels, carousels, newsletters) is rendered from that
object, checked, and published only after a human sign-off.

**Status (28 Sep 2026): everything runs.** What you still add: an LLM key (Claude or any OpenAI-compatible
provider) and, optionally, keys for FRED and web search. Without a key, `demo` mode walks through the whole app with
real data tools but scripted "reasoning".

## Start

```bat
start_finmedia.bat            :: Windows: sets up .venv, builds the web app on first run, opens http://127.0.0.1:8020
```

or by hand:

```bash
python -m venv .venv && .venv\Scripts\activate      # (Linux/Mac: . .venv/bin/activate)
pip install -e ".[dev]"
cd web && npm install && npm run build && cd ..
copy .env.example .env                               # then add your keys
finmedia serve                                       # http://127.0.0.1:8020
finmedia serve --provider demo                       # try everything without an LLM key
pytest                                               # 51 tests, no network, no paid calls
```

## Add the keys

1. Copy `.env.example` to `.env` (same folder; git-ignored) and fill in what you have:
   - `ANTHROPIC_API_KEY` for Claude, **or** `OPENAI_COMPAT_API_KEY` for Groq / OpenAI / OpenRouter / Together.
   - `FRED_API_KEY` (free) for US and global macro series.
   - One of `TAVILY_API_KEY`, `BRAVE_SEARCH_API_KEY`, `SERPAPI_API_KEY` for web search.
   - Optional: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (alerts), `FINMEDIA_APP_TOKEN` (web app password).
2. Choose the LLM in `config/settings.yaml` → `agent.provider` (`anthropic`, `openai_compat`, `demo`). For
   `openai_compat`, set `base_url` and the model names, and their prices for the budget guard.
3. Restart `finmedia serve`. **Settings** in the web app shows which keys are present and which tools they unlock.

No key is needed for NSE filings, results and shareholding, RBI, SEBI, PIB, the US Fed, World Bank data, GDELT, or
the Economic Times / Moneycontrol / Mint news feeds. All of these were checked live on 28 Sep 2026. BSE's API
refuses scripted access (HTTP 403), so it is not used.

## The web workspace

| Page | What it does |
|---|---|
| **Research** | Chat with the lead researcher. You see its plan, every tool call and result live. **Steer** it mid-run or **stop** it. Follow-ups revise the Research Object into a new version. Options: depth (quick / standard / deep: step and rupee limits) and **as-of date** (time-travel: nothing after that date is used). The **Budget / policy study** button runs the milestone-1 playbook. |
| **Library** | Every Research Object with its versions, claims ledger, content built from it, and evidence log. Memos open as HTML (internal edition, or a research edition with directional views MARKED for compliance). |
| **Content studio** | Drafts in four formats, the automatic checks, human edits, approvals (editor / compliance / RA) and the publish record. Drafts built on an older object version are marked **stale**. |
| **Memory** | The firm's point-in-time research memory: events, expectations, reactions, market-structure changes, findings, notes. Search "as of" any date; corrections supersede, nothing is overwritten. |
| **Sources** | Background collectors (status, errors, run now), upload a PDF, fetch a document by URL, search everything collected. |
| **Scoreboard** | Every directional claim, scored against what actually happened once its horizon passes (vs NIFTY, via PTIS). |
| **Settings** | LLM provider, keys, services, budget and spend, and which research tools are available. |

## How a research run works

```
question ─► lead researcher (LLM with tools, up to N steps / ₹ cap)
              │  memory_search · memory_similar · documents_search · read_stored_document
              │  regulator_feed (RBI/SEBI/PIB/Fed) · nse_announcements · nse_results · nse_result_figures (XBRL)
              │  nse_event_calendar · nse_corporate_actions · nse_shareholding · fetch_document (PDF/HTML)
              │  fred_series · worldbank_indicator · news_search (+GDELT) · web_search
              │  ptis_macro_state · ptis_sector_map · ptis_sector_state · ptis_sector_series · ptis_event_study
              │  ptis_beneficiaries · fno_cost · consult_panel (7 seats) · red_team · run_budget_study
              ▼
         submit_research ─► provenance check (numbers, evidence refs, source URLs) ─► one chance to fix
              ▼
         Research Object vN saved · claims → ledger · events / findings / structure changes → memory
              ▼
         content drafts ─► checks (numbers ⊆ object, voice, disclosure, sources) ─► compliance items ─► sign-off ─► published
```

Rules the code enforces:
- **The LLM never supplies a number.** Every number in the object must appear in a tool result of the run. The
  panel's and the content's numbers are checked the same way.
- **Point in time.** Tools hide data after the as-of date. A time-travel run never writes into the memory.
- **Budget.** Each call is checked against the worst case before it runs: a per-run rupee cap by depth, plus the
  monthly research cap (`budget.research_llm_cap_inr`, **₹12,000 is a placeholder until you confirm it**) and the
  media cap for content.
- **Publish gate.** Directional views and named stocks are kept (the founder's decision), but marked. Any such
  item requires a `compliance` or `ra` sign-off; an editor's approval is enough only when there are none.

## Other entry points

```bash
finmedia ask "What did SEBI change for F&O traders this month?" --depth quick   # the same agent in the terminal
finmedia ask --thread 3 "Now compare with the 2024 measures"                     # follow-up in a conversation
finmedia collect --all                                                           # run every collector once
finmedia mcp                                                                     # the data tools over MCP for Claude Code / Desktop
finmedia research "Union Budget 2026" --asof 2026-02-01                          # milestone-1 budget study (CLI)
finmedia research-postmortem                                                     # score due claims
finmedia costs                                                                   # month-to-date spend
```

The original Reel pipeline (`ingest`, `triage`, `brief`, `reel`, `daily`, `lint`, `strategy-test`, `fno-cost`) is
unchanged.

**MCP (use the tools from Claude Code).** Add to a project's `.mcp.json`:
`{"mcpServers": {"finmedia": {"command": "C:/Users/abhis/Downloads/Finmedia/.venv/Scripts/finmedia.exe", "args": ["mcp"], "env": {"FINMEDIA_ROOT": "C:/Users/abhis/Downloads/Finmedia"}}}}`.
Only data tools are exposed; paid LLM tools stay inside the budget-guarded web runs.

**PTIS quant tools** need the PTIS research bridge running (from the PTIS repo:
`set PTIS_ENV=test` then `python -m research_bridge.server`). Without it, research still runs and those tools are
switched off.

## Layout

```
src/finmedia/
  ai/            providers.py (Claude, OpenAI-compatible, demo) · __init__.py (budget-guarded AI facade)
  agent/         lead.py (agent loop, steering, limits) · tools.py (registry) · models.py (Research Object)
                 provenance.py · objects.py (versions, claims, memory writes)
  content/       engine.py (formats, checks, approvals, stale flags) · memo.py · models.py
  sources/       market.py (NSE, XBRL, documents, FRED, World Bank, GDELT, web search) · rss.py · gdelt.py · inbox.py
  server/app.py  FastAPI: REST + live event stream + the built web app
  memory.py      point-in-time memory + document search (SQLite FTS5)
  collectors.py  scheduled collection, health, alerts, daily claim scoring
  runs.py        conversations, background runs, event bus
  research/      milestone-1 budget / policy sector study (playbook)
  store.py (SQLite) · costs.py (budget guard) · env.py (.env keys) · notify.py (Telegram) · mcp_server.py · cli.py
web/             React + TypeScript app (npm run build → web/dist, served by finmedia serve)
prompts/agent/   lead researcher, panel, red team, personas.yaml   prompts/content/  house rules + format prompts
config/          settings.yaml (providers, budget, depth, server, collectors) · sources.yaml · lint_rules.yaml
```

## Docs

Architecture and decisions: [`docs/research-desk-architecture.md`](docs/research-desk-architecture.md). Strategy
and content: [`docs/strategy-research-2026-09.md`](docs/strategy-research-2026-09.md) ·
[`docs/instagram-first-launch.md`](docs/instagram-first-launch.md) ·
[`docs/automated-video-pipeline.md`](docs/automated-video-pipeline.md) ·
[`docs/hindi-script-guide.md`](docs/hindi-script-guide.md) · [`docs/budget-lean-launch.md`](docs/budget-lean-launch.md).

*Research and education. Nothing produced by this project is investment advice until the publish gate (SEBI RA
registration or a compliance sign-off) says so.*
