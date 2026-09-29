# Finmedia Research Desk — Architecture, Decisions and Status

*Written 27 Sep 2026. It records every decision taken while designing the Deep Research Desk, what is built, what is not, and the order of work. It extends [`intelligence-system-architecture.md`](intelligence-system-architecture.md) and supersedes it where they differ (see §2).*

> **Status (28 Sep 2026): BUILT — the workspace runs end to end.** On the founder's instruction the build resumed
> before Model 4's deployment finished. What remains is adding keys: an LLM provider (Claude or OpenAI-compatible)
> and optionally FRED and web search. See §11 for what was built and what is still open.

---

## 1. What Finmedia is for

**The engine.** A research engine that studies any market topic the way a firm would: economist, sector specialist, portfolio manager, risk manager, hedger, technical trader and quant manager.
- **Topics:** a budget, an RBI or Fed decision, a sector's news, a technology shift, or a question such as "why did this setup stop working: a phase or a permanent shift?"
- **Outputs:** research oriented to wealth creation, wealth protection and opportunities.

**The business around the engine.**
- A public media brand, the evidence lab (§6).
- Paid research once the SEBI Research Analyst (RA) licence is obtained.
- B2B research licensing.
- A tight relationship with PTIS (§7).

## 2. Architecture decisions and why

The original architecture document says "a workflow first, agents only where judgment is needed". That still holds for repeatable events. But the founder needs open, on-demand research that no fixed workflow can anticipate. The resolution:

| Decision | Reason |
|---|---|
| **A lead-researcher agent** (Claude, on the Agent SDK) is the default for open questions. It plans, delegates to sub-agents, calls tools and writes the result | Open questions ("how do algos beat retail?") cannot be pre-scripted |
| **Fixed workflows become playbook tools** the lead researcher can call (milestone 1's budget study is the first) | Repeatable events stay cheap, testable and consistent |
| **Every capability is a tool server (MCP):** `ptis-quant`, `market-sources`, `research-memory` | The same tools work from Claude Code/Desktop today and from Finmedia's own app later |
| **The LLM never supplies a number.** Every number in an output must match a tool result or a quoted source document | Credibility; the milestone-1 verifier generalises to a provenance check against the run's tool log |
| **Primary sources first.** News is used to find events; filings, circulars and official documents are what we cite | Accuracy and legal safety |
| **Point-in-time everything.** Every stored record carries `known_at` | Honest history, and the ability to re-run any study "as of" a past date without leakage |
| **One verified Research Object feeds every output** (§5) | No reinterpretation between a memo, a video and a Reel |

### Target shape

```
            YOU (prompt, steer mid-run, approve)
                         │
     RESEARCH WORKSPACE (phase 1: Claude Code/Desktop · phase 2: Finmedia web app)
                         │
     LEAD RESEARCHER (Claude) ── sub-agents: collectors · 7 analyst personas · skeptic · CIO
                         │  every call goes through tools
  ┌──────────────┬───────┴────────┬──────────────────┬───────────────┐
  ptis-quant     market-sources   web (secondary)    research-memory  playbooks
  (prices, event (NSE/BSE filings, (news, previews,   (typed, point-   (budget study,
  studies, PIT   results, SEBI/   expectations)      in-time store)   results, RBI…)
  fundamentals,  RBI, budget docs,
  strategy       Fed/FRED, MoSPI)
  forensics)
                         ▲
  BACKGROUND: daily collectors → events and facts into memory · post-mortem scores every past claim
```

## 3. Research memory (the long-term moat)

The memory is typed, point-in-time and **append-only**. Nothing is overwritten; a correction is a new record that supersedes the old one. It lives in one Postgres database with pgvector.

| Record | Holds |
|---|---|
| Document | Raw primary document, hash, URL, published_at, fetched_at |
| Event | What happened, when, type, entities, stage (proposal → final → effective), **mechanism tags** |
| Expectation | What the market expected beforehand (survey, consensus, options-implied move), with source and time |
| Reaction | Measured abnormal returns at T+1/5/20/60 (from `ptis-quant`) |
| Market-structure change | CAS, expiry rules, STT, lot sizes, US 23/5 trading, …, **linked to the strategies it affects** |
| Finding | A research conclusion: hypothesis / supported / killed / superseded, evidence, review date |
| Claim | Every directional call, scored later by the post-mortem |

**Rules for the memory:**
- **Similarity search uses mechanism tags** (who pays, which channel, proposal vs final), not only text embeddings. Otherwise it retrieves events that *sound* alike instead of events that *work* alike.
- **Collectors should start early.** Data can be backfilled later, but what we knew and concluded at the time cannot.

## 4. Research modes and outputs

**Modes:**
- event study;
- company deep dive (business model, annual report, order book, what management said this call vs last);
- structure forensics (temporary phase, regime-dependent, or structural shift);
- market structure and participants;
- theme / technology.

**Output types**, all rendered from one Research Object:
- investment memo;
- event intelligence report;
- historical study;
- sector deep dive;
- market post-mortem;
- trading research;
- content package.

Every memo includes a "what this means for our books" section.

## 5. Research Object and content

- **One verified object, many presentations.** YouTube scripts, Reels, carousels and newsletters only render the object. Every number in a script must trace back to it.
- **Revisions propagate:** if an object is corrected, everything built from it is flagged.
- **Full disclosure (founder's decision):** directional views and stock calls go into content in full; nothing is hidden. Every directional or stock-level claim carries a **marker** in the object. The marker does not hide anything; it makes a manual compliance pass a quick filter instead of a hunt.
- **Publish gate:** the SEBI RA licence, or, until it is granted, the team's manual review and sign-off.
- **Content engine (later):** long-form research documentaries (10–20 min), Reels (30–120 s), charts and animations, source cards, research screenshots. The founder's disclosed AI twin is the recognisable interface, not the product.

## 6. Positioning: the evidence lab

Research findings (sources in the business report, §9):
- 78.6 lakh individuals traded F&O in FY26 and 87.7% lost money.
- Nine in ten households do not invest (complexity, fear of loss, lack of trust).
- 59% of new investors are under 30, mostly outside the metros.
- Backtesting tools already exist (Streak, AlgoTest, FakeTrades).

**The gap:** evidence, in Hindi, of what works in Indian markets after costs, *when* it works, why setups stop working, and how backtests lie.

**Content rules:**
- **Lead with what works** (founder's correction: viewers want what makes money, not autopsies).
- **Mix:** about 60% "what works and how to use it", 25% "protect yourself" (costs, scam maths, why setups die), 15% events and the scoreboard.
- **Verdict format:** *Works / Doesn't work / Works only when.* Every video ends with something the viewer can use.
- **"Works" means historical evidence with its conditions,** never a promise of returns. No specific stock or fund picks before the RA licence.
- **Test the audience assumption:** in the first 90 days, publish "what works" and "what failed" titles side by side and compare click-through, watch time and sign-ups.
- **Money ladder:**
  1. free videos;
  2. WhatsApp/newsletter list;
  3. a method-only course (legal before the RA licence; no live trading rooms, calls, return claims or P&L screenshots);
  4. RA research subscription;
  5. B2B research desk;
  6. later, evidence brand → money management (the Capitalmind path).
- **Defer the paid data tool:** its data licence costs more than it earns until the list is large.

## 7. The PTIS relationship

PTIS was designed as a multi-user **personal trading partner**:
- the "eye" (market perception) with a grounded reasoner;
- a proactive coach that flags the user's own kind of setup as it forms, shows blind spots, watches positions and guards discipline;
- an autonomous virtual trader;
- user-taught strategies tested per stock;
- behavioural replay of the user's trades.

It is market-grounded and designed to be more objective than its user.

**One shared core, three surfaces.** The shared core is the data, point-in-time memory, quant engine, research protocol and claims ledger. It feeds:
1. the firm's own trading (private);
2. Finmedia (the public evidence lab);
3. PTIS (the personal partner SaaS).

**How each side feeds the other:**
- **Finmedia teaches the general truth; PTIS makes it personal and live:**
  - teach *your* strategy and see it tested on *your* stocks;
  - "is today that kind of market?";
  - the coach catches *your* late entries;
  - replay shows why *you* lose.
- **Viewer strategy submissions are PTIS's taught-strategy feature.** With consent, the aggregate becomes content and a unique dataset.
- **Finmedia's point-in-time news, filings and macro memory gives PTIS's price-only reasoner the real "why".**
- **Public, timestamped, scored calls** are a genuine forward test for PTIS research.
- **The collectors' market-structure timeline** feeds PTIS drift monitoring and kill switches.

**Guardrails:**
1. A wall around the firm's live book: its rules and positions are never published (thinly traded small caps; manipulation risk).
2. An RA restricted list: no trading a security from 30 days before to 5 days after a report on it; disclose holdings.
3. Viewer questions go to a separate queue; they never steer the PTIS research agenda.
4. Every submitted strategy test is registered and deflated for the number of trials.
5. PTIS stays a tool, not a black-box advice product.

**Regulatory flags (legal review needed before launch):**
- Personalised position advice to paying users ("exit now", "size up") is likely Investment Adviser territory, not just RA.
- User-defined-rule alerts are fine.
- Auto-execution for users falls under the retail algo framework.
- Republishing exchange data needs a licence.
- User data falls under the DPDP Act.

## 8. What is built (milestone 1) and what is not

### Built on branch `research-desk-m1` — 33 tests pass

**Budget / sector research desk** (`src/finmedia/research/`):

| File | Role |
|---|---|
| `cases.py` | Analogue events strictly before the report date |
| `quant.py` | The quant pack from the PTIS bridge, rounded to 2 decimals. It reports how many analogue events were actually measured and why others were not |
| `pipeline.py` | Scoper → fact extractor (quotes verified verbatim) → quant pack → 7 personas in parallel → skeptic → CIO |
| `verify.py` | Every number must round-match the pack or a cited fact; regenerate once, then flag |
| `render.py` | Internal report (watermarked, PDF via Edge) and a public draft built from structured data only, linted for advice language and stock names |
| `models.py` | Strict output schemas |

**Other pieces:**
- **Prompts:** `prompts/research_*.md` plus `prompts/personas/*.md` (economist, sector specialist, portfolio manager, risk manager, hedger, technical trader, quant manager).
- **Store:** `research_runs` and `claims` tables.
- **Budget:** a separate research budget pool (`research_llm_cap_inr`, kind `llm_research`) that cannot eat the media budget. **₹12,000 is a placeholder the founder has not confirmed.**
- **CLI:**
  - `finmedia research "<topic>" --asof YYYY-MM-DD [--docs …] [--sectors …] [--estimate-only]`;
  - `finmedia research-postmortem` (scores claims from the report-date close).
- **Case library:** `data/cases/union_budgets.yaml`, 35 budgets 1997–2026 with verified dates. 2024-07-23 and 2004-02-03 are correct; common online lists get these wrong. Sector tags are pending.
- **Business simulation:** `scripts/business_viability_sim.py` (§9).
- **PTIS bridge client:** `src/finmedia/tools/ptis.py`.

> **Dependency:** the PTIS research bridge the desk calls lives in the PTIS repo (`research_bridge/`: a read-only FastAPI app on 127.0.0.1:8010, every call takes `asof`). **It is not committed in PTIS yet.** Start it with `PTIS_ENV=test PYTHONPATH=. python -m research_bridge.server` from the PTIS repo.

**Known data limit:** PTIS's NIFTY history starts in September 2007, so pre-2008 budgets cannot be measured. As of 2025-01-31, 17 of 28 full budgets are measured. A benchmark proxy built from the stock panel was rejected, because it would stack one proxy on top of survivor-heavy baskets.

**Real result example** (as of 2025-01-31): in the month after past budgets, Power lagged NIFTY by a median −1.98% and beat it in only 2 of 17 (t −2.23).

### Not built yet
- The Case Extractor agent (sector tags from budget speeches, with founder approval).
- A live run: needs `ANTHROPIC_API_KEY` and a confirmed research budget.
- The time-travel test on Budget 2025. The model's training covers it, so the real test is the next live event (an RBI policy, Budget 2027) with claims logged beforehand.
- Everything in §2–§5 beyond milestone 1:
  - the lead-researcher agent;
  - the tool servers (MCP);
  - the research memory;
  - the collectors;
  - the Research Object with claim markers;
  - the content engine;
  - the workspace UI.

## 9. Business case (simulation, 27 Sep 2026)

**Method.** 20,000 simulated futures over 36 months, with parameters from public benchmarks (YouTube ad rates, paid-newsletter conversion and churn, course conversion, SEBI rules). The pass rule was set before running: covers running costs by month 24 in ≥ 50% of futures, **and** ≥ ₹2 lakh a month by month 36 in ≥ 40%.

| Plan | Covers costs by m24 | Year-3 average monthly income (median) | Chance of ₹2L+/month |
|---|---|---|---|
| Base | 43% | ₹45k (month-36 snapshot) | 18% |
| Instagram-fed list + B2B from month 6 | 62–68% | ₹85k | 23% |
| **Evidence lab** (the same + method-only course) | 66–68% | **₹1.42L** | **39%** |
| No RA licence (ads only) | 3% | ₹1k | 0% |

**What the numbers mean:**
- **Year one earns almost nothing.** Money arrives in year 2–3, and it is 50–90% recurring once it does.
- **The outcome is mostly an audience bet.**
- **The RA licence is decisive.** The owned list and B2B are the biggest levers; price and language barely matter.
- **The plan narrowly fails the pre-set bar;** it passes only if the Hindi niche also improves audience odds, which the 90-day title test measures.

**Checkpoints:**
- **Month 6:** RA granted, a list of 300+, the desk demoed to 5+ firms.
- **Month 12 stop rule:** under 5,000 YouTube subscribers **and** a list under 500 **and** no paying client. Stop the media spend (loss capped near ₹4L).
- **Month 12 scale rule:** 10,000+ subscribers, a 1,000+ list, 10+ paying subscribers, or a B2B pilot.

**Recommendation:** build the research engine regardless (it serves the firm's own research), and gate the media spend.

Full report with sources: the founder's private "Finmedia Business Odds" page (ask the founder for access).

## 10. Build order when work resumes

1. **Research memory** (Postgres schema, append-only, `known_at`) and the claims ledger, as the shared core.
2. **`ptis-quant` tool server:** wrap the research bridge and add strategy forensics (rolling edge, structural-break test, market-structure overlay).
3. **Research-desk skill for Claude Code** (personas, memo format, provenance rule). **This is the first usable version: ask any research question.**
4. **`market-sources` tool server:** NSE/BSE filings and results, SEBI/RBI, budget documents, Fed/FRED first.
5. **Background collectors and the post-mortem scheduler.** These run while the founder is away, so use the same supervisor and alert pattern as PTIS's live loop.
6. **Research Object with claim markers**, then the content engine.
7. **Finmedia's own web workspace** (team roles: analyst, compliance, RA).

**Open decisions for the founder:**
- the monthly research budget;
- whether collectors run on the PC or a small cloud server;
- whether to pay for a consensus-estimates source or start with options-implied expectations.

## 11. Build of 28 Sep 2026 — the working workspace

**What changed from the plan above.**
- **SQLite with FTS5, not Postgres + pgvector.** Free, zero-setup, and the same schema can move later. Similarity
  uses mechanism tags plus full-text search; no embedding API needed.
- **The workspace is Finmedia's own web app (phase 2) from day one,** because the founder asked for the chat UI. The
  same tools are also exposed over MCP (`finmedia mcp`) for Claude Code / Desktop (phase 1).
- **Any LLM.** `agent.provider` = `anthropic` (Claude), `openai_compat` (Groq, OpenAI, OpenRouter, Together, local
  Ollama) or `demo` (no key; scripted walk-through over real tools, for testing).

**Built and tested (51 tests, no network, no paid calls):**

| Part | Where | Notes |
|---|---|---|
| Lead researcher agent | `agent/lead.py` | Tool loop; live events; steer mid-run; stop; step and rupee caps per depth; forced submission at the limit; follow-ups revise the object; interrupted histories repaired |
| 26 tools + submit | `agent/tools.py` | Memory (4), primary sources (8: RBI/SEBI/PIB/Fed feeds, NSE announcements / results / XBRL figures / calendar / actions / shareholding, documents by URL), data (FRED, World Bank), secondary (news, GDELT, web search), PTIS quant (6), F&O cost, analyst panel (7 seats), red team, budget playbook |
| Provenance check | `agent/provenance.py` | Numbers must appear in the run's tool results; evidence refs must exist; source URLs must have been fetched. One chance to fix, then saved as `flagged` |
| Research Objects | `agent/objects.py` | Versioned; claims to the ledger with directional markers; memory updates (skipped for time-travel runs); older content marked stale |
| Research memory | `memory.py` | Typed, append-only, point-in-time (`known_at`), supersede-not-overwrite, tag similarity, document search |
| Collectors | `collectors.py` | 12 sources checked live on 28 Sep 2026 (BSE refuses scripted access); health, failure streaks, Telegram alert, daily claim scoring |
| Content engine | `content/` | YouTube, Reel, carousel, newsletter from one object; numbers must be in the object; compliance items (directional views, named stocks, promise words) require a compliance/RA sign-off; editor-only approval when none; publish record |
| Web app | `web/` + `server/app.py` | Research chat with live timeline, library, content studio, memory, sources, scoreboard, settings (keys and tools status), optional app token |

**Still open (founder decisions or later milestones):**
- Keys: an LLM key (and choice of provider), FRED, one web-search key.
- Confirm the monthly research budget (₹12,000 placeholder) and the per-depth run caps.
- **No live LLM run has been made yet**, so the agent's research quality is untested. Before trusting it:
  1. run a few questions at `quick` depth;
  2. read the evidence logs;
  3. tune `prompts/agent/*.md`.
- The Anthropic and OpenAI-compatible paths are tested against mocked responses only.
- Case Extractor for budget sector tags (G1), expectations/consensus source, video layer, publishing APIs.
- Hosting: collectors only run while `finmedia serve` is running on this PC. A small Indian server is needed for
  24x7 collection.
