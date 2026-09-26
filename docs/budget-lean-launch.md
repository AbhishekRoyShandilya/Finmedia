# Finmedia — Lean Launch Budget

*⚠️ **Current rule: all-in monthly cap of ₹10,000–12,000. See §10, which overrides the monthly figures in §3 and §9.***

*For a low-budget start: spend only on what unblocks the next step, and unlock each extra spend with a result. Prepared 26 Sep 2026. Prices are approximate (converted at ~₹88/$) and should be re-checked before purchase. Supersedes the rough MVP table in [`strategy-research-2026-09.md`](strategy-research-2026-09.md) §7.*

---

## 0. The answer in one line

**Voice-first plan (founders record and edit):** about **₹6,000–11,000 one-time plus ₹2,000–10,000/month**, roughly **₹40,000–60,000 for the first 6 months** (see the ultra-lean scenario in §7).

**Digital-twin plan (your AI face and voice, automated videos; the chosen direction, see §9):** about **₹8,500–14,500 one-time plus ₹7,000–24,000/month**, roughly **₹80,000–1,10,000 for the first 6 months**. No video editor needed, because the pipeline does the editing.

In both plans, SEBI Research Analyst registration later adds about **₹28,000–45,000 in fees and a legal check**, plus a **₹1 lakh fixed deposit** that is locked (as a lien), not spent. It's only needed when we start company-specific views (month 3–6).

The biggest cost is **founder time**, not money.

---

## 1. What we deliberately *don't* buy at the start

| Skip for now | Why | Free substitute |
|---|---|---|
| AI avatar subscription (HeyGen etc.) | *Voice-first plan only.* In the chosen digital-twin plan this becomes a core cost (§9), using **your own** face with disclosure, never a fictional persona | Founder's own voice over charts and documents |
| Hindi AI voice (ElevenLabs etc.) | *Voice-first plan only.* In the digital-twin plan we clone **your** voice (§9) | Record yourself |
| English dubbing service | YouTube offers **free auto-dubbing and multi-language audio tracks** | YouTube's built-in dubbing (check that Hindi→English works for our channel; disclose that it's AI-dubbed) |
| Paid news feeds (Reuters, Bloomberg) | Expensive; we use primary sources anyway | SEBI/RBI/IRDAI/NSE/BSE websites, PIB, MoSPI API, FRED, GDELT (all free) |
| Paid market-data license | Needed for redistribution and for the automated product, not for the first 10 videos | Free official sources for research; licensed charts later (see §4) |
| Studio, camera, lights | No face on camera at the start | A good mic in a quiet room |
| Paid ads / promotion | Wasted before the format is proven | Shorts, collaborations, WhatsApp Channel |
| Company incorporation | Not required to start a channel or to register as an individual RA | Start as individuals; incorporate once revenue starts |
| Full automated system build | Weeks of work before a single video | **Manual-first:** run the playbooks by hand with Claude and a spreadsheet, automate the steps you repeat most |

---

## 2. One-time costs

| Item | Cost (approx.) | When | Needed? |
|---|---|---|---|
| USB/dynamic microphone + pop filter | ₹4,000–8,000 | Week 1 | ✅ Yes. Audio quality matters more than video for this format |
| Domain name (for newsletter/site) | ₹800–1,200/year | Week 1 | ✅ Yes |
| NISM Series XV (Research Analyst) exam | ₹1,500 per attempt | Month 1–2 | ✅ Yes. The workbook is free from NISM |
| SEBI RA registration fee (individual) | ~₹15,000 + GST | Month 2–4 | When company-specific content starts |
| RA deposit (FD lien, up to 150 clients) | **₹1,00,000 locked, not spent** (earns FD interest) | With RA registration | Same as above |
| Compliance consultation with a securities lawyer (one review of our formats and disclaimers) | ₹10,000–25,000 | Before the RA launch | Strongly recommended |
| Company incorporation (Pvt Ltd), if and when needed | ₹7,000–15,000 incl. professional fees (estimate) | After first revenue | Later |

**One-time total**
- **Before RA: ~₹6,000–11,000**
- **At the RA launch: + ~₹28,000–45,000 in fees and legal, + ₹1 lakh FD lien**

---

## 3. Monthly running costs

### 3a. Tools

| Item | Lean choice | Monthly (approx.) |
|---|---|---|
| **AI for research and scripts, phase 0 (months 1–2)** | Claude Pro subscription, used manually to run the playbooks and draft Hindi scripts | ~$20 (≈ ₹1,800). Check current India pricing |
| **AI for the automated pipeline, phase 1 (month 3+)** | Claude API with a lean design (see §5) | ~$40–100 (≈ ₹3,500–9,000) |
| Video editing software | DaVinci Resolve (free) or CapCut (free tier) | ₹0 |
| Thumbnails and graphics | Canva free, or Canva Pro (₹3,999/year) | ₹0–333 |
| Charts | Python (free) using official data | ₹0 |
| Music and stock footage | YouTube Audio Library, Pexels (free) | ₹0 |
| Server for the pipeline (month 3+) | Small VPS ($6–12) + free-tier Postgres (Supabase/Neon; check limits) | ₹500–1,000 |
| Newsletter | Substack or Beehiiv free tier | ₹0 |
| WhatsApp Channel, YouTube, Instagram | Free | ₹0 |

**Tools total: ~₹2,000/month (months 1–2) → ~₹5,000–10,000/month (month 3+)**

### 3b. People: the real budget decision

| Option | Monthly (approx.) | When it makes sense |
|---|---|---|
| **A. Founders edit everything** | ₹0 | Start here. Learn what our videos need before paying someone else |
| **B. Pay per Short, founders edit the long videos** | ₹300–500 per Short × 15–20 = **₹5,000–10,000** | Once we're making 4+ Shorts a week |
| **C. Junior editor on retainer** | **₹15,000–28,000** | Once there are signs of traction (see §6 gates) |

---

## 4. Data: start free, pay only when needed

| Stage | Source | Cost |
|---|---|---|
| **Months 1–3 (manual research)** | Official websites (SEBI, RBI, IRDAI, NSE/BSE announcements and daily reports, PIB, Budget), MoSPI eSankhyiki API, FRED, GDELT, Alpha Vantage free tier (limited requests per day; it's already connected to this workspace) | ₹0 |
| **Charts in videos** | Charts built from official data, or embedded charts from a charting platform whose terms allow it. Don't screenshot broker terminals | ₹0 to low |
| **Month 4+ (event studies at scale)** | NSE/BSE-authorized data vendor for clean historical EOD data (get quotes from TrueData, Global Datafeeds, or NSE's own EOD/historical product) | Quote-based. Budget ₹2,000–15,000/month depending on license |

Automated scraping of exchange websites isn't a free substitute; check each site's terms. For the manual phase, reading and downloading official reports for research is fine.

---

## 5. How we keep AI costs low (when we automate)

Current Claude API list prices per million tokens (input / output): **Haiku 4.5: $1 / $5 · Sonnet 5: $2 / $10 · Opus 5: $5 / $25.**

A lean month (~200 filings a day triaged, ~7 deep analyses a week, scripts and edits):

| Step | How we keep it cheap | Est. monthly |
|---|---|---|
| **Pre-filter** | Plain code rules first (keywords, company list, document type) drop ~80–90% of filings before any AI sees them | $0 |
| **Triage** of the remaining ~200 documents/day | Cheapest model tier, short prompts | ~$25–30 |
| **Deep analyses** (~7/week) | Best model only here; **prompt caching** for the big stable parts (sector packs, style guides) | ~$40–50 |
| **Scripts and edits** | Mid tier where quality holds | ~$10–20 |
| **Historical backfills** | **Batch API** (~50% cheaper, runs overnight) | Occasional |

**Total: ~$75–100/month (≈ ₹6,500–9,000).** It could be lower after measuring. Treat these as estimates and check real usage in the first month.

---

## 6. Spend gates: unlock money with results

| Unlock | Gate (all must be true) |
|---|---|
| Canva Pro + pay-per-Short editing | 8+ long videos published; posting schedule held for 4 weeks |
| Claude API pipeline + VPS | The manual playbooks are stable; the same steps are repeated every week |
| **SEBI RA registration + legal review** | Audience asking for company-specific views, **or** 1,000+ newsletter/WhatsApp subscribers ready for a paid tier |
| Junior editor retainer | 2+ videos above 25k views, **or** 3 months of steady growth in returning viewers |
| Market-data license | Event-study automation is ready to use it; the B2B pilot needs clean data |
| AI avatar / digital twin (optional) | A real, named host is established and a daily format needs scaling |

---

## 7. Six-month budget scenarios

| Scenario | What it includes | 6-month total (approx.) |
|---|---|---|
| **Ultra-lean** | Founders voice and edit everything; Claude Pro, then lean API from month 3; free tools; no RA yet | **₹40,000–60,000** |
| **Recommended lean** | Ultra-lean + Canva Pro + pay-per-Short editing from month 3 + RA registration and legal consult in months 4–6 | **₹1,00,000–1,40,000** (+ ₹1 lakh FD lien, locked) |
| **Comfortable** | Recommended + junior editor from month 4 + data vendor from month 4 + ElevenLabs for dubbing polish | **₹2,00,000–2,80,000** (+ ₹1 lakh FD lien) |

The **recommended lean** plan fits the ₹50k–1.5L MVP range discussed earlier, excluding the ₹1 lakh FD lien (locked, not spent).

---

## 8. Month-by-month (recommended lean)

| Month | Spend on | Approx. spend |
|---|---|---|
| 1 | Mic, domain, NISM exam, Claude Pro | ₹8,000–13,000 |
| 2 | Claude Pro | ₹2,000 |
| 3 | Claude API + VPS, Canva Pro, pay-per-Short editing | ₹12,000–20,000 |
| 4 | Running costs + RA registration fee + legal consult (if gate met) | ₹35,000–55,000 (+ ₹1L FD lien) |
| 5 | Running costs | ₹12,000–20,000 |
| 6 | Running costs | ₹12,000–20,000 |

---

## 9. Digital-twin plan (chosen direction, 26 Sep 2026)

The founder's face and voice are cloned once, and videos are produced by the automated pipeline in [`automated-video-pipeline.md`](automated-video-pipeline.md). This replaces the video-editor cost with tool subscriptions.

### One-time
| Item | Cost (approx.) |
|---|---|
| Microphone + pop filter | ₹4,000–8,000 |
| Soft light for the twin recording (a 4K-capable phone is enough as the camera) | ₹2,000–4,000 |
| Domain | ₹800–1,200/year |
| NISM Series XV exam | ₹1,500 |
| **Total** | **₹8,500–14,500** |

### Monthly
| Item | Months 1–2 (build + test) | Months 3–6, semi-automatic | Months 3–6, fully automatic |
|---|---|---|---|
| Claude (Pro subscription → API) | ~₹2,000 | ~₹6,500–9,000 | ~₹6,500–9,000 |
| ElevenLabs Creator (voice clone) | ~₹2,000 | ~₹2,000 | ~₹2,000+ |
| HeyGen (avatar) | ~₹2,550 (Creator) | ~₹2,550 (Creator) | ~₹8,700–11,000+ (API/higher tier; confirm pricing) |
| Server / rendering | ₹0 (laptop) | ~₹500–1,000 | ~₹2,000–3,500 |
| Canva Pro | ~₹333 | ~₹333 | ~₹333 |
| **Total** | **~₹7,000** | **~₹12,000–15,000** | **~₹20,000–26,000** |

### Six-month total
| Path | Total (approx.) |
|---|---|
| Semi-automatic all six months | **~₹80,000–90,000** |
| Semi-automatic → fully automatic from month 4 | **~₹1,00,000–1,10,000** |
| Either path + SEBI RA fees and legal consult (month 4–6) | **+ ₹28,000–45,000** (+ ₹1 lakh FD lien, locked) |

**At full target volume (1 Reel/day + 8–10 long videos of 12–15 min):** the video layer rises to **~₹11,000–13,000/month** (HeyGen Pro or Creator + ElevenLabs Pro) if the avatar step stays semi-automatic, or **~₹19,000–23,000** fully automatic via HeyGen's API. Months 3–6 then total roughly **₹20,000–25,000/month (semi-automatic)**, bringing the six-month total to **~₹1,00,000–1,25,000** before RA costs. The detailed math is in [`automated-video-pipeline.md` §8b](automated-video-pipeline.md#8b-cost-at-our-target-volume-1-reel-a-day--810-long-videos-a-month).

**Spend gate for going fully automatic:** the semi-automatic pipeline has shipped 8+ videos, and the manual avatar step is the main bottleneck.

---

## 10. Hard cap: ₹10,000–12,000 per month, all-in (decided 26 Sep 2026)

This section **overrides** the monthly figures above. Everything (AI, voice, avatar, data, news, server, design) must fit under **₹12,000/month**, with a target of ~₹10,000.

### 10a. Do we need news, report or data subscriptions? No.

| Need | Paid option we **skip** | What we use instead (free) |
|---|---|---|
| Breaking news / event detection | Reuters, Bloomberg, paid news APIs, premium newspaper subscriptions | NSE/BSE announcement pages, SEBI/RBI/IRDAI/PIB releases, GDELT (global), Google News RSS for detection only |
| Reports & research | Paid research databases, broker-report services | Regulator reports (SEBI studies, RBI Bulletin/FSR/annual report), company annual reports, investor presentations, earnings-call transcripts (all free on exchanges) |
| Economic data | Paid macro terminals | MoSPI eSankhyiki API, RBI DBIE downloads, FRED, Alpha Vantage free tier |
| Market prices | Paid data vendor license | Free official daily exchange reports for research; licensed data only after revenue |

Our edge is **reading primary documents better**, not having a paid news feed. (A founder may personally keep one newspaper subscription for reading, but the pipeline doesn't need it.)

### 10b. The capped monthly budget

| Item | Plan | ₹/month (approx., at ₹88/$) |
|---|---|---|
| **LLM (Claude)** | Claude Pro subscription while semi-manual; later the API with a **hard monthly spend limit of ~$30** (strict code pre-filtering, cheapest model for triage, Opus only for flagship scripts, prompt caching) | ~1,800–2,600 |
| **Voice clone** | ElevenLabs **Creator** ($22, ~121k credits ≈ 120 min of speech). Overage/usage billing **switched off** | ~1,950 |
| **Avatar** | HeyGen **Creator** ($29, 600 credits ≈ 30 avatar-min at Avatar IV). Clips generated in the web app, **not** the API | ~2,550 |
| **Server** | Small VPS for the pipeline; render videos on the founder's laptop | ~600 |
| **Design** | Canva free (Pro ₹333 only if needed) | 0–333 |
| **Domain** | Yearly, spread per month | ~100 |
| **Data, news, reports** | Free sources (10a) | 0 |
| **Buffer** (retakes, occasional extra) | Reserved, not auto-spent | ~1,500 |
| **Total** | | **~₹8,500–9,500, + ₹1,500 buffer = ₹10,000–11,000** |

### 10c. What content volume fits under the cap

The voice plan (~120 minutes of speech a month) is the binding limit. So:
- **8 long videos of ~12 min** (≈ 96 min of narration), plus
- **30 Reels, of which ~20 are cut from the long videos** (reusing the same voice and avatar clips, so almost no extra cost) and **~10 are original** (≈ 8 min of narration).
- **≈ 105 min of narration + ~15% retakes ≈ 120 min.** That fits ElevenLabs Creator.
- Avatar: ~15–20% face time on long videos + ~40% on original Reels ≈ **18–22 avatar minutes ≈ 360–440 credits.** That fits HeyGen Creator's 600 (unused credits roll over one month).

**Going above this** (10 long videos of 15 min each) needs ElevenLabs Pro (+ ~₹6,800/month). **Only do that once revenue covers it** (spend gate).

### 10d. How we stop costs from exploding

1. **Only fixed-price subscriptions or hard-capped usage.** No open-ended pay-as-you-go:
   - set a **monthly spend limit in the Anthropic Console** for the API;
   - keep **usage-based billing off** in ElevenLabs;
   - HeyGen Creator can't buy extra credit packs, so it's naturally capped.
2. **Render once.** The avatar and voice are generated **only after the script is approved** (Gate G2). Regenerate only the scenes that fail QA, never the whole video.
3. **Code before AI.** Keyword, company-list and document-type rules drop most filings before any AI model sees them.
4. **Right model for the job.** The cheapest model for triage; a mid model for briefs; the best model only for final flagship scripts. Cache the large stable prompts (sector packs, style guides).
5. **Reuse.** Reels are cut from long videos wherever possible; one research brief feeds the long video, Reels, newsletter and WhatsApp post.
6. **Weekly cost check.** Cost per video (AI tokens + voice credits + avatar credits) goes in a simple sheet. If a month is on track to pass ₹12,000, the pipeline pauses new renders until the next cycle.
7. **Annual billing only after month 3,** once the tools are proven (roughly 15–20% cheaper, but it needs cash up front).

### 10e. One-time costs (unchanged)
Mic, soft light, domain and NISM exam: **~₹8,500–14,500 one-time**. SEBI RA fees and legal review (~₹28,000–45,000) and the ₹1 lakh FD lien come **later**, as separate one-time costs when the RA gate is met, not from the monthly cap.

---

## Sources

- [SEBI RA deposit requirement (LexiBox)](https://www.lexibox.in/ra/deposit-requirement-for-research-analysts-ras/) · [Compliance Calendar: deposit in place of net worth](https://www.compliancecalendar.in/learn/deposit-requirement-in-place-of-net-worth-certificate-for-research-analysts-ras)
- [NISM: prerequisites for SEBI RA registration](https://www.nism.ac.in/blog/prerequisites-for-becoming-a-sebi-registered-research-analyst)
- [ElevenLabs pricing](https://elevenlabs.io/pricing) · [ComparEdge: ElevenLabs plans 2026](https://comparedge.com/tools/elevenlabs/pricing)
- [Canva Pro price in India 2026](https://catlistmedia.com/2026/02/26/canva-pro-price-india-2026-guide/)
- [Fueler: freelance video editing rates, India 2026](https://fueler.io/blog/freelance-video-editing-rates-india-vs-global-market) · [Fueler: video editor pay guide](https://fueler.io/blog/video-editor-salary-in-india-freelance-and-full-time-pay-guide)
- [TrueData pricing page](https://www.truedata.in/price) · [NSE paid EOD/historical data](https://www.nseindia.com/static/market-data/eod-historical-data-subscription)
- [TechCrunch: YouTube multi-language audio for all creators](https://techcrunch.com/2025/09/10/youtubes-multi-language-audio-feature-for-dubbing-videos-rolls-out-to-all-creators/)
- Claude API prices: Anthropic's current model pricing (Haiku 4.5, Sonnet 5, Opus 5)
- Digital-twin tool pricing (HeyGen, ElevenLabs, Remotion): see the sources in [`automated-video-pipeline.md`](automated-video-pipeline.md)
