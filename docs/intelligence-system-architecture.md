# Finmedia Intelligence System — Architecture

*The research engine behind every video, report and tool: clean data in; mapped, historical, explained intelligence out. Designed 26 Sep 2026. Companions: [`content-research-system.md`](content-research-system.md) (knowledge-base layers and accuracy rules), [`../system/event_playbooks.yaml`](../system/event_playbooks.yaml) (machine-readable playbooks).*

---

## 0. What this system must do

1. **Collect clean data** from official and licensed sources: exchange filings, earnings, deals, flows, policy, budget, regulators, macro, global rates, commodities, and technology.
2. **Understand each event** like a senior analyst would. Not "paste the news," but *what changed, who it touches, through which mechanism, over what time horizon*.
3. **Map the impact** onto the whole market, sectors, individual stocks, and **participant groups** (retail, FIIs/FPIs, DIIs, promoters, prop/algo traders).
4. **Pull history:** what happened the last N times something similar happened, measured by code, not remembered by an LLM.
5. **Explain it as a story:** a daily-life anchor, a supply-chain or manufacturing example, a quotable mechanism, in our Hindi expert voice.
6. **Treat different news differently.** An earnings surprise, a regulatory proposal, a 10-year policy and a new technology behave completely differently, so each gets its **own playbook**.
7. **Teach the audience when to react to what**, and how to build their own version of the system.

### Five design principles

| # | Principle | Why |
|---|---|---|
| 1 | **The LLM is the analyst and writer, never the database.** Every number comes from a tool call against our data | LLMs misremember numbers and dates. Our credibility depends on every figure being traceable |
| 2 | **A workflow first, agents only where judgment is needed.** Code routes events through fixed steps; LLM agents do the thinking inside those steps | Predictable, testable, cheaper, easier to audit than one free-roaming agent |
| 3 | **Playbooks, not one generic pipeline.** A router classifies each event and sends it to a type-specific playbook | Different news has different reaction speeds, drivers and history |
| 4 | **Point-in-time everything.** We store what was known *when*, down to the minute | Needed for honest history ("what did the market know at 6:10 pm?") and honest evaluation |
| 5 | **Humans sign off; the system proposes.** Named human review at fixed gates; RA sign-off for company-specific views | Quality, legal safety (SEBI), and trust |

---

## 1. High-level architecture

```
┌──────────────────────────── 1. INGESTION ────────────────────────────┐
│ Exchanges · Earnings/XBRL · Transcripts · Deals · Shareholding ·      │
│ Flows (FII/DII, participant OI) · Regulators · Govt/Budget · Macro ·  │
│ Global (Fed, US data, FX) · Commodities · News signals · Tech/research │
└───────────────┬──────────────────────────────────────────────────────┘
                ▼
┌──────────────────────── 2. NORMALIZE & STORE ────────────────────────┐
│ Raw archive (original file + hash + fetched_at + published_at IST)    │
│ Parse (PDF/XBRL/HTML → text + tables) · Entity resolution (ISIN,      │
│ NSE symbol, BSE code, aliases) · Market-session tagging · Dedupe      │
│                                                                        │
│ Stores:  Documents+vectors │ Time-series │ Knowledge graph │           │
│          Event DB          │ Case library│ Claims ledger   │           │
└───────────────┬──────────────────────────────────────────────────────┘
                ▼
┌─────────────────────── 3. INTELLIGENCE LAYER ────────────────────────┐
│  Triage & Router ──► Playbook (one of 11) ──► Agent team for that     │
│                                               playbook:               │
│   Fact Extractor · Exposure Mapper · Participant Analyst ·            │
│   Historian (+Quant tools) · Sector Specialist · Skeptic ·            │
│   Verifier · Compliance · Storyteller · Editor                        │
│                         ▼                                              │
│             Research Brief (every claim cited)                         │
└───────────────┬──────────────────────────────────────────────────────┘
                ▼   human gates G1/G2/G3
┌────────────────────────── 4. OUTPUTS ─────────────────────────────────┐
│ Event cards · Pre-Market Desk · Flagship scripts (Hindi) · Reels ·    │
│ WhatsApp/newsletter · Public event tracker · (later) RA notes, API    │
└───────────────┬──────────────────────────────────────────────────────┘
                ▼
┌────────────────────────── 5. LEARNING LOOP ───────────────────────────┐
│ Post-mortem agent at T+1 / T+5 / T+30 → outcomes into Event DB and    │
│ claims ledger → playbook & prompt improvements → evaluation suite     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data layer: sources and how to get them

Priority **P0** = needed for the MVP; **P1** = months 2–4; **P2** = later.

| Category | What | Source & access | Frequency | Notes | Priority |
|---|---|---|---|---|---|
| **Exchange announcements** | Corporate announcements, outcomes of board meetings, orders, M&A, credit ratings, auditor changes | NSE & BSE corporate filings (public filing pages; for automated production use, an exchange data license or authorized vendor. Check each site's terms before scraping) | Real time | Store the original PDF and the exchange timestamp; tag pre/during/post-market | **P0** |
| **Financial results** | Quarterly/annual results | **XBRL filings** on NSE/BSE (machine-readable). Since Q4 FY25, NSE's "Integrated Filing" consolidates results, related-party transactions and audit qualifications | Quarterly | Parse XBRL, don't OCR the PDFs | **P0** |
| **Earnings calls** | Audio + transcripts, investor presentations | Exchange filings: SEBI LODR requires the audio/video within 24 hours and the transcript within 5 working days | Quarterly | Diff each call against the previous one (guidance and tone changes) | P1 |
| **Deals & insider activity** | Bulk/block deals, insider trading (PIT) and takeover-code (SAST) disclosures, promoter pledges | NSE/BSE daily reports & filings | Daily | Key for "Before the Move" | **P0** |
| **Ownership** | Shareholding pattern: promoter / FPI / MF / other DII / retail | Exchange XBRL filings | Quarterly | Powers retail/FII impact mapping | **P0** |
| **Flows** | FII/DII provisional cash flows; **participant-wise F&O open interest** (Client / DII / FII / Pro); NSDL FPI data | NSE daily reports (participant OI typically published ~5–6 pm IST); NSDL | Daily | Who is positioned where | **P0** |
| **Prices & derivatives** | EOD/intraday prices, corporate actions, option chains, index constituents over time | **NSE/BSE-authorized data vendor** (license required for redistribution) | EOD → intraday | Keep adjusted and unadjusted series; index membership by date | **P0** |
| **Regulators** | SEBI, RBI, IRDAI, PFRDA, IFSCA: circulars, consultation papers, orders, press releases, board-meeting outcomes | Official websites (RSS where offered) | Real time | Stage-tracking: proposal → final → effective | **P0** |
| **Government & Budget** | PIB releases, e-Gazette notifications, Budget documents, CBDT/CBIC notifications, GST Council decisions, ministry data (e.g. PPAC for fuel) | Official sites | Real time / event | Budget day = special playbook | **P0** |
| **India macro** | CPI, IIP, GDP, jobs; money, credit, rates, FX reserves | **MoSPI eSankhyiki API** (open, no auth; MoSPI also runs a beta MCP server); **RBI DBIE** (downloads, no official public API); FBIL/CCIL benchmarks | Monthly / weekly | Release calendar feeds the scheduled-event playbook | P1 |
| **Global macro & rates** | Fed/ECB decisions, US CPI/jobs, US yields, dollar index, USD/INR | FRED, Federal Reserve, BLS, US Treasury; **Alpha Vantage** (already connected to this workspace: FX, US macro, commodities, news sentiment) | Event / daily | Transmission to India via FPI flows, rupee, sectors | P1 |
| **Commodities** | Crude, gas, metals, agri; MCX contracts | Licensed vendor (MCX/LME/COMEX); EIA; World Bank Pink Sheet (monthly); Alpha Vantage | Daily | Feeds input-cost / manufacturing chains | P1 |
| **News signals** | Global and Indian news for *detection* (not republication) | **GDELT** (free, global, updated every 15 min, 100+ languages); a licensed Indian news feed later; company press releases | Continuous | Use news to *find* events, then go to the primary document. Never quote news as the source when a primary exists | P1 |
| **Technology & future finance** | AI, tokenization, payments, DLT pilots, market-structure research | BIS/IMF/RBI/SEBI papers, RBI UMI/CBDC updates, arXiv, SEC EDGAR (global tech filings), industry bodies | Weekly | Feeds the "Next-Gen" playbook | P2 |
| **Our own data** | Event DB, claims ledger, experiments, audience questions | Internal | Continuous | The long-term moat | **P0** |

> **Connector note:** a Groww MCP server is configured for this workspace but **isn't authorized yet**. Authorize it in the claude.ai connector settings if we want to explore it for Indian market data during research. It doesn't replace a licensed data feed for publishing.

### 2a. The company master (build this first)

One row per listed company:
- **Identifiers and names:** ISIN, NSE symbol, BSE code, legal name, aliases (e.g. "Policybazaar" → PB Fintech).
- **Classification:** NSE industry classification.
- **Membership over time:** index membership history, F&O eligibility history.

Every document and every event is linked to this master. Entity resolution is where most news pipelines silently fail.

---

## 3. Storage layer

| Store | Holds | Suggested tech (MVP) |
|---|---|---|
| **Raw archive** | Original files, hashes, fetch and publish timestamps | Object storage (S3-compatible) |
| **Document store + vectors** | Parsed text/tables, chunk embeddings for retrieval | Postgres + pgvector |
| **Time-series** | Prices, flows, OI, macro, commodities | Postgres + TimescaleDB |
| **Knowledge graph** | Companies ↔ sectors ↔ revenue drivers ↔ regulators ↔ commodities ↔ macro variables ↔ suppliers/customers ↔ owners | Postgres tables first (edges table); a graph DB only if needed |
| **Event DB** | Every event with classification, exposures, reactions, follow-ups (schema §5) | Postgres |
| **Case library** | Curated historical case files | Postgres + raw archive |
| **Claims ledger** | Every published claim, timestamp, evidence, outcome | Postgres |

One Postgres instance with extensions covers the MVP. Split later only when load demands it.

### 3a. Knowledge graph: the "financial understanding" backbone

Main relationships (each edge carries `source`, `as_of`, `confidence`):

```
Company ─SEGMENT_REVENUE(%)──► Segment
Company ─EXPOSED_TO(direction, sensitivity, rationale)──► Variable (crude, USDINR, repo rate, steel, US yields…)
Company ─REGULATED_BY──► Regulator (SEBI, RBI, IRDAI, TRAI, DGCA…)
Company ─SUPPLIES_TO / BUYS_FROM──► Company
Company ─COMPETES_WITH──► Company
Company ─OWNED_BY(category, %, quarter)──► OwnerCategory (promoter, FPI, MF, retail…)
Company ─CONSTITUENT_OF(from, to, weight)──► Index
Sector ─DRIVEN_BY──► Variable
Variable ─TRANSMITS_TO(lag, sign)──► Variable   (e.g. crude → India CPI → RBI policy)
```

How it gets built:
- An **Extractor agent** reads annual reports, investor presentations and results, and proposes edges with citations.
- A human analyst approves them.
- We start with the ~200 most-traded companies and the ~15 most regulation- and commodity-sensitive sectors.

---

## 4. The intelligence layer

### 4a. Triage & Router: deciding *what kind* of news this is

For every new document or event, the Router produces:

```yaml
event_type:       regulatory.proposal.commission_cap     # taxonomy in event_playbooks.yaml
playbook:         regulatory_change
materiality:      0-100   # expected market significance
novelty:          new | update | duplicate
horizon_class:    H0 | H1 | H2 | H3
scheduled:        true | false
primary_entities: [ISINs / sectors / variables]
status:           proposal | final | effective | rumour
needs_human_now:  true | false   # e.g. materiality ≥ 70 after market close
```

**Reaction-horizon classes** (the core of "different news behaves differently"):

| Class | Horizon | Typical examples | What decides the price reaction |
|---|---|---|---|
| **H0** | Minutes to 1 day | Earnings, RBI/Fed decisions, CPI prints, sudden company news | **Surprise vs. expectation**, not the headline |
| **H1** | Days to weeks | Guidance changes, regulatory proposals, block deals, rating changes | Re-pricing of earnings estimates, positioning, drift |
| **H2** | Months to quarters | Final regulations, commodity cycles, rate cycles, index/market-structure changes | Actual earnings impact as quarters report |
| **H3** | Years | Structural policy (PLI, capex programs, tax regime), technology adoption, demographics | Adoption curves, capital allocation, competitive shifts |

### 4b. The eleven playbooks

Each playbook has its own data pulls, agent team, analysis steps, history rules and output formats. The full definitions are in [`system/event_playbooks.yaml`](../system/event_playbooks.yaml). Summary:

| # | Playbook | Horizon | The key question | Signature analysis |
|---|---|---|---|---|
| 1 | **Scheduled data & policy** (RBI MPC, Fed, CPI, GDP) | H0 | Actual vs. expected, and did the *forward guidance* change? | Surprise measure; statement wording changes; transmission map |
| 2 | **Earnings & guidance** | H0–H1 | Did results and **guidance** beat what was priced in? | Options-implied move before results vs. actual move; comparing this earnings call with the previous one |
| 3 | **Company-specific unscheduled** (orders, M&A, management change, capex, fund-raise) | H0–H1 | How big is this relative to the company, and was it known already? | Size vs. revenue/market cap; information timeline; pre-announcement drift |
| 4 | **Regulatory change** (SEBI/RBI/IRDAI/TRAI…) | H1–H2 | Proposal or final? Which revenue lines change, by how much? | Stage tracking; exposure % of revenue; scenario math; historical dilution between proposal and final |
| 5 | **Fiscal & structural policy** (Budget, PLI, tax, government capex) | H1–H3 | Money announced vs. money actually spent; who really benefits? | Allocation vs. disbursement history; beneficiary mapping; multi-year order flow |
| 6 | **Macro & global transmission** (rates, USD/INR, US yields, geopolitics) | H0–H2 | Through which channel does this reach Indian sectors and flows? | Transmission graph; sector sensitivity from history; FPI flow response |
| 7 | **Commodity & input-cost shock** | H1–H2 | Who pays, who passes it on, and with what lag? | Input-cost share (from annual reports); inventory lag; pricing power → the **manufacturing example chain** |
| 8 | **Market structure & flows** (index changes, F&O rules, lock-in expiries, IPO supply, MSCI/FTSE) | H0–H2 | Is there a *mechanical*, predictable flow? | Estimated passive flows vs. average daily volume; timing calendar |
| 9 | **Corporate actions & special situations** (buyback, open offer, delisting, rights, demerger) | H1–H2 | What's the math for a shareholder, and the retail-specific angle? | Acceptance ratios, tax treatment, historical outcomes |
| 10 | **Governance & red-flag shocks** (auditor exit, pledge invocation, SEBI order, fraud allegation) | H0–H2 | Is it on the official record? What happened in similar cases? | Pattern library of past cases; **legal review before publishing** |
| 11 | **Technology & next-gen finance** (AI, tokenization, payments, DLT, EVs, semis) | H3 | Who builds it, who benefits, who gets disrupted, and when? | Adoption stage (the window model); value-chain mapping; Indian exposure at sector level |
| — | **Rumour / unverified** | — | Can it be confirmed from a primary source? | **Verification gate.** Not published as fact; may become "noise vs. signal" education |

### 4c. The agent team

Each agent is a focused LLM step with tools and a strict output schema. The playbook decides which agents run and in what order.

| Agent | Job | Key tools | Model tier (to be measured) |
|---|---|---|---|
| **Triage & Router** | Classify, score materiality, dedupe, route | Company master lookup, recent-events search | Fast/cheap tier (Haiku 4.5 or Sonnet 5), or Opus 5 at low effort. Measure both |
| **Fact Extractor** | Pull the exact facts from the primary document (numbers, dates, status, effective dates) **with citations** | Document parser; Claude citations on document blocks | Sonnet 5 / Opus 5 |
| **Sector Specialist** (one per sector pack) | Explain the business mechanism in this sector: value chain, unit economics, what really drives profits | Sector knowledge pack (cached), knowledge graph | Opus 5 |
| **Exposure Mapper** | 1st-order (direct), 2nd-order (suppliers, customers, competitors), 3rd-order (macro, sentiment) exposure with direction, size and rationale | Knowledge graph queries, segment revenue data | Opus 5 |
| **Participant Analyst** | Impact on **retail vs FPI vs DII vs promoter vs prop/algo**: who owns it, who's positioned, who reacts fastest | Shareholding pattern, FII/DII flows, participant OI, delivery % | Opus 5 |
| **Historian** | Find comparable past events (similarity criteria stated), request the event study | Event DB search, case library | Opus 5 |
| **Quant (tools, not an LLM)** | Returns, abnormal returns, base rates (N, median, range, hit rate), scenario arithmetic, options-implied moves | Python functions over the time-series DB | Deterministic code |
| **Skeptic / Red Team** | Argue the other side: confounders, what's already priced in, proposal-vs-final, overreach | All of the above outputs | Opus 5 (high effort) |
| **Verifier** | Check every number and claim in the brief against sources; flag anything unsupported | Claims vs. citations, DB lookups | Opus 5 |
| **Compliance** | Tag E / M / RA tier; flag recommendation language, price targets, return claims, anchor-style phrasing | Rules + LLM check | Sonnet 5 |
| **Storyteller** | Turn the brief into a Hindi expert script: daily-life opening, manufacturing/supply-chain example, analogies, the 12 moves, thesis line | Style guides (cached), analogy library | Opus 5 |
| **Editor** | Anchor test heuristics, banned phrases, readability, numbers-per-sentence rule | Style rules | Sonnet 5 |
| **Post-mortem** | At T+1/T+5/T+30: compare what we said vs. what happened; log outcomes and lessons | Claims ledger, time-series | Sonnet 5 + Quant tools |

**Model guidance.** Default to Claude Opus 5 for reasoning-heavy steps, with adaptive thinking. Use a cheaper tier only for high-volume, simple steps (triage, formatting), and only after measuring that quality holds. Opus at low effort often matches a smaller model at high effort. Treat the tiers above as starting hypotheses to measure.

### 4d. How the agents get "deep financial understanding"

1. **A strong base model** for reasoning (above).
2. **Sector knowledge packs:** a curated 20–40 page brief per sector (business model, value chain, KPIs, regulators, typical sensitivities, landmark historical episodes, analogies). Written by humans, checked against filings, and kept stable so they can be **prompt-cached**, which makes reusing them on every event cheap.
3. **Retrieval (RAG)** over our document store: the latest filings, prior events, case files.
4. **Tools for all numbers:** SQL/time-series/event-study functions. The model asks; code answers.
5. **A "gold analyses" library:** 30–50 exemplary, human-written analyses (one or more per playbook) used as reference examples.
6. **An evaluation suite** (§7) to measure whether all of this actually works, before we trust it.

Fine-tuning isn't needed to start. Revisit it once we have hundreds of human-approved analyses.

### 4e. Claude API features to use

| Need | Feature | Note |
|---|---|---|
| Every claim traceable to a page | **Citations** on document blocks | Citations can't be combined with structured-output formatting in the same call. Extract with citations first, then structure in a second step |
| Reliable machine-readable outputs (event object, exposure matrix) | **Structured outputs** / strict tool schemas | Validate against our schemas |
| Reusing big stable context (sector packs, style guides, playbooks) | **Prompt caching** | Keep stable content first in the prompt; volatile event data last |
| Backfilling years of historical events, nightly re-scoring | **Message Batches API** | ~50% cost; async |
| Agent loops with our tools (DB queries, event study) | **Tool Runner** in the Python SDK | Our code hosts the tools and controls the workflow |
| Deep, open-ended investigations (flagship research) | Tool-use agent loop with task budgets | Only for the flagship "investigation mode" |
| Scheduled nightly jobs | Our own scheduler (Prefect/cron). Managed Agents scheduled deployments are an option later | Start simple |

---

## 5. The event object (what every playbook produces)

```yaml
event_id: EVT-2026-09-23-IRDAI-001
detected_at: 2026-09-23T18:24:00+05:30
published_at: 2026-09-23T18:10:00+05:30      # from source
market_session_at_publish: post_market
source: {type: regulator, name: IRDAI, doc_url: ..., doc_hash: ...}
event_type: regulatory.proposal.distribution_economics
playbook: regulatory_change
status: proposal            # proposal | final | effective | diluted | withdrawn | stayed
horizon_class: H1
materiality: 85
facts:                      # from Fact Extractor, each with citation
  - {claim: "Life insurers' EoM to 15% of GDPI within 2 years", cite: "p.x"}
exposures:                  # from Exposure Mapper
  - {entity: PB Fintech, order: 1, direction: negative, size: high,
     rationale: "commission/take-rate compression", evidence: [...], confidence: 0.8}
participants:               # from Participant Analyst
  - {group: FPI, holding_pct: ..., note: "..."}
  - {group: retail, holding_pct: ..., note: "..."}
analogues:                  # from Historian + Quant
  similarity_criteria: "regulator-imposed caps on distribution economics, India, 2010–2026"
  n: ...
  reaction: {T+1: {median: ..., range: [...]}, T+20: {...}, T+60: {...}}
  dilution_base_rate: "x of n proposals were diluted before final"
skeptic_notes: [...]
open_questions: [...]
what_would_change_view: [...]
compliance_tier: M          # E | M | RA
outputs: [pre_market_desk, flagship_candidate, reels_x3]
follow_ups: [{date: ..., check: "final regulation published?"}]
outcome: {T+1: ..., T+30: ...}   # filled by Post-mortem
```

---

## 6. From brief to content: the storytelling engine

The Storyteller doesn't summarize the brief. It follows a **story recipe** chosen by playbook:

| Playbook | Story recipe | Daily-life anchor examples | "Manufacturing example" style |
|---|---|---|---|
| Earnings | "What the market expected vs. what the company *said about the future*" | "Your Zomato order price" for a delivery company | Unit economics of one order |
| Regulatory | "Who pays to acquire a customer, and what happens when the rules change" | The phone number an insurance site asked for | Commission flow: customer → distributor → insurer |
| Commodity | "Raw vs. finished: why the input fell but your bill didn't" | Petrol pump meter, paint shop, tyre prices | Crude → refinery → petrol/diesel → truck freight → sabzi price |
| Macro/global | "How a decision in Washington reaches your SIP" | Rupee rate on a remittance app, gold price at the jeweller | Fed → US yields → FPI selling → rupee → import costs |
| Fiscal/structural | "Money announced vs. money actually spent" | A new highway or metro near you | Government order → contractor → cement & steel → jobs |
| Market structure | "The flow nobody decides, because it's automatic" | "Your index fund buys this stock whether you like it or not" | Index inclusion → passive funds → forced buying on a known date |
| Tech/next-gen | "Who builds it, who benefits, who gets disrupted, and how you prepare" | UPI → next: tokenized assets; ChatGPT → AI research desk | Adoption stages; skills and positioning |

The Storyteller has an **analogy library** (toll plaza, IRCTC Tatkal, sabzi mandi, cricket DRS, society maintenance bill…). Each analogy is tagged with the concept it explains and checked so it doesn't mislead.

**Output formats per event:** event card → Pre-Market Desk segment → Reel scripts → flagship candidate (if the topic scores ≥ 12/15 on the playbook's topic rubric) → newsletter/WhatsApp brief.

---

## 7. Evaluation: proving the system is good before we trust it

### 7a. Time-travel replay (the key test)
- Take **past events** (the seed case library plus the last 3 years of major events).
- Rebuild the knowledge base **as it was at that moment** (point-in-time data only).
- Run the full pipeline, then compare its outputs with what actually happened.
- **Leakage warning:** the LLM may already "know" what happened in older events from its training data. Test mainly on events **after the model's training cutoff**, or anonymize company names and dates in older tests.

### 7b. Metrics per playbook

| Metric | Measures |
|---|---|
| **Exposure recall / precision** | Did we list the companies that actually moved most? Did we list companies that didn't move? |
| **Direction accuracy** (first-order exposures) | Up/down correct at T+1 / T+20 |
| **Calibration** | When we say "high confidence," are we right more often? |
| **Factual accuracy** | % of claims the Verifier confirms against sources (target 100% for published numbers) |
| **Latency** | Time from publication to event card / to draft script |
| **Human rubric** | Senior reviewer scores: insight, clarity, mechanism correctness, story quality |

The live pipeline also feeds this: every published event gets a Post-mortem, so the evaluation set grows every week.

---

## 8. Teaching the audience *when to react to what*

The event DB lets us replace opinions with measured **reaction profiles**. Each playbook produces an audience-facing rule of thumb, **measured from our own data** (the values below are starting hypotheses until our event studies confirm them):

| News type | How fast the price reacts | Who usually reacts first | Hypothesis for a long-term investor | Hypothesis for a trader |
|---|---|---|---|---|
| Earnings surprise | Minutes | Algos and institutions | Don't chase the first move; judge the **guidance change** | Speed disadvantage; the open is usually already priced |
| Regulatory **proposal** | Immediate overreaction possible | Everyone at once | Wait for the **final** rule; check how often proposals were diluted | Watch whether the stock recovers or keeps falling |
| Final regulation | Slow, over quarters | Analysts update models | Watch the next 2–4 quarters of earnings | Limited edge |
| Fiscal/structural policy | Years | Narrative traders first, fundamentals later | Track money *spent*, not announced | Headline spikes often fade |
| Macro/global shock | Hours to days | FPIs and algos | Usually noise for long horizons unless it changes rates/earnings | Transmission trades via FX/rates |
| Commodity shock | Weeks to quarters (margin lag) | Commodity desks | Check pricing power and pass-through | Input-cost lag creates windows |
| Index/market-structure flows | Known dates | Arbitrage desks | Mostly irrelevant long term | Predictable but crowded |
| Tech/next-gen | Years | Early builders | Prepare skills and positioning early (the window model) | Hype cycles, few durable trades |

This becomes:
- a **content franchise**, "कब React करें?";
- a field on every **public event card** ("reaction profile: fast / slow / structural");
- over time, a feature of the PTIS product.

### 8a. "How to work with the system, and build your own"
- Each public event card shows *how* we analyzed it (sources, analogues, what would change our view). This teaches the method.
- The **"Build Your Own Edge"** series rebuilds simplified versions: a circular watcher, an event card generator, a basic event study.
- We open-source small starter tools, keeping the full knowledge graph and event DB as our moat.

---

## 9. Human gates & compliance

| Gate | When | Who | Checks |
|---|---|---|---|
| **G1: Triage** | Materiality ≥ 70, or any governance/red-flag event | On-duty analyst | Is it real? Is it primary-sourced? Should it go to fast track? |
| **G2: Research brief** | Before any script | Senior analyst | Facts, exposures, analogues, skeptic notes |
| **G3: Publish** | Before publishing | Editor, plus the SEBI RA for company-specific views | Compliance tier, disclosures, anchor test, legal review for red-flag stories |

---

## 10. Build plan

| Phase | Weeks | Deliverables | Done when |
|---|---|---|---|
| **0. Foundation** | 1–4 | Company master; ingestion for SEBI/RBI/IRDAI + NSE/BSE announcements + EOD prices + FII/DII + participant OI; raw archive; event DB schema; Router v1 (playbooks 3, 4, 8) | Every new filing is linked to a company, timestamped, classified within 15 min |
| **1. Analysis core** | 5–10 | Knowledge graph for 200 companies / 15 sectors; sector packs v1 (insurance, banks/NBFC, OMC/energy, IT, pharma, auto, metals, FMCG, capital goods/defence, telecom, capital-market companies, real estate); Historian + Quant event-study engine; Fact Extractor with citations; Storyteller (Hindi) + Editor; G1–G3 workflow | IRDAI-type events produce a cited brief and a Hindi Pre-Market Desk script in ≤ 3 hours |
| **2. Breadth & rigor** | 11–20 | Playbooks 1, 2, 5, 6, 7, 9, 10; global/macro/commodity feeds; Participant Analyst; Skeptic + Verifier; Post-mortem loop; time-travel eval suite v1 | Eval dashboard live; 100% of published numbers verifier-confirmed |
| **3. Next-gen & audience tools** | 21–30 | Playbook 11 (tech/next-gen); public event tracker with reaction profiles; "कब React करें?" franchise data; open-source starter tools | Public event cards updating daily |
| **4. Premium** | after RA registration | RA-reviewed company views, scorecard, B2B pre-market desk, API | First paying B2B pilot |

### MVP stack
- **Language and data:** Python. Postgres (+ TimescaleDB, pgvector). S3-compatible object storage.
- **Pipeline:** Prefect (or cron to start) for ingestion jobs. PDF/XBRL parsers. Streamlit or Metabase for the internal analyst console.
- **LLM:** Anthropic Python SDK (Claude API with the Tool Runner, citations, structured outputs, prompt caching, Batches).
- **Rough LLM cost at MVP scale** (~1,500 documents triaged a day, ~15 deep analyses a day): on the order of **$300–1,000/month** before optimization. This is an estimate; measure real usage in phase 0 and tune models, effort and caching from there.

---

## Sources

- [SEBI LODR earnings-call disclosures (transcript within 5 working days)](https://blog.alfafinder.com/learn/earnings-call-transcript-india-sebi-guide/)
- [NSE guidance note on analyst/institutional investor meet disclosures](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Guidance%20note%20on%20disclosures%20pertaining%20to%20analysts,%20institutional%20investors%20meet%20and%20best%20practices.pdf)
- [NSE corporate filings: financial results](https://www.nseindia.com/companies-listing/corporate-filings-financial-results)
- [India XBRL filings explained (NSE/BSE, integrated filing)](https://www.tigzig.com/vigil/india-xbrl-filings)
- [Participant-wise open interest on NSE: guide](https://www.oidata.in/blog/participant-wise-open-interest-nse)
- [MoSPI eSankhyiki portal (PIB)](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2029708) · [eSankhyiki catalogue](https://esankhyiki.mospi.gov.in/catalogue-main) · [MoSPI MCP server (GitHub)](https://github.com/nso-india/esankhyiki-mcp)
- [RBI DBIE](https://data.rbi.org.in/)
- [GDELT data](https://gdeltproject.org/data.html)
- NSE data licensing and authorized vendors: see [`strategy-research-2026-09.md`](strategy-research-2026-09.md) §3d
