# Finmedia — Automated Video Pipeline (Digital Twin)

*How videos get made without the founder recording or reading anything: researched script → your cloned voice → your digital-twin avatar → data visuals → assembled video → published. Designed 26 Sep 2026. Companions: [`intelligence-system-architecture.md`](intelligence-system-architecture.md) (where scripts come from), [`hindi-script-guide.md`](hindi-script-guide.md), [`budget-lean-launch.md`](budget-lean-launch.md).*

---

## 0. The model in one paragraph

You record **once** (a 1–2 day session to create your digital twin: face + voice). After that, every video is produced by the pipeline:

1. the research system writes a cited Hindi script with a scene-by-scene plan;
2. your **cloned voice** reads it;
3. your **digital-twin avatar** appears for about 15–25% of the video (opening, turns, key insight, close);
4. the rest is **data visuals**: charts, highlighted official documents, money-flow animations;
5. code assembles, captions, labels and uploads the video.

**Your job per video is about 30–45 minutes of approval, not recording**: pick the topic, check the facts, watch the final cut. That approval step isn't optional; see §6.

---

## 1. Why this design (and not a 100% talking avatar)

| Decision | Reason |
|---|---|
| **Your own face and voice**, cloned with your consent | YouTube's Jul 2026 policy doesn't pay for *AI personas* giving finance advice. A **real, named person** using an AI twin, disclosed, is on the safe side. It's also what builds trust in a market full of deepfake scams |
| **Avatar on screen only ~15–25% of the time** | (1) Our signature is the *receipts*: documents and data on screen. (2) Less avatar time means lower cost (avatar tools bill per minute). (3) Less "uncanny valley" risk; small lip-sync flaws matter less |
| **Human approval on every video** | You're legally responsible for what your twin says (SEBI, IT Rules). YouTube also demonetizes mass-produced, unreviewed AI content |
| **Every video disclosed as AI-generated** | Required by India's IT Rules 2026 (continuous visible label) and YouTube's synthetic-content policy. We set it automatically on upload |

---

## 2. The one-time twin recording session

| What | How much | Notes |
|---|---|---|
| **Consent video** | Short, as instructed by the avatar tool | Required by HeyGen and similar tools; must be the same person as the footage |
| **Avatar footage** ("looks") | 2–5 minutes per look, at least 1080p/30fps (4K better). Record 2 looks: a desk setup and a standing/explainer setup | A modern phone is enough; use steady soft light and the good mic. Speak naturally, with calm hand movement, like explaining to a friend |
| **Voice samples** for a professional voice clone | At least 30 minutes; **1–2 hours is recommended** for a high-quality clone. Single speaker, quiet room | Read our own Hindi scripts (with English financial terms) so the clone learns the words we actually use: SIP, repo rate, F&O, crore… |
| **Refresh** | Every 6–12 months, or if your look changes a lot | |

Equipment: the microphone from the budget, a phone that records 4K, a soft light (₹2,000–4,000), a plain or bookshelf background.

---

## 3. Tool choices

| Layer | Primary choice | Why | Alternatives |
|---|---|---|---|
| **Voice clone** | **ElevenLabs Professional Voice Clone** (Creator plan, $22/month) | Best-known quality for cloned voices; pronunciation dictionaries for English terms inside Hindi; timestamps for captions | HeyGen's built-in voice (simpler, possibly lower Hindi quality). Test both |
| **Digital-twin avatar** | **HeyGen Avatar IV digital twin** (consent flow built in; Hindi lip-sync; API available) | Most realistic avatars in 2026 reviews; accepts our own audio so the voice stays consistent | Synthesia personal avatar (steadier, less expressive). Open-source lip-sync models later, if we have GPU and engineering time (cheaper per minute, more work) |
| **Assembly / editing** | **Remotion** (videos as code, in React). Free for individuals and companies up to 3 people | Data-driven charts, templated scenes, captions, 16:9 + 9:16 from one scene plan | FFmpeg + MoviePy (Python), or a paid video API (Shotstack, Creatomate) |
| **Captions** | Word timestamps from the voice step, or forced alignment | Hindi captions (Devanagari) burned in for Shorts; caption track uploaded for long-form | Whisper-based alignment |
| **Stock footage & music** | Pexels API (free); a pre-cleared music set from the YouTube Audio Library | Free and licensed for use | — |
| **Publishing** | **YouTube Data API** (upload, schedule, **`status.containsSyntheticMedia = true`**); **Instagram Graph API** for Reels (Professional account) | The AI disclosure is set by code on every upload | Manual upload as a fallback |

> **Pick by test, not by review.** In week 1, generate the same 60-second Hindi script with 2–3 voice/avatar combinations. Show them to 5 people who haven't worked on it. Choose the one they find **clearest and most trustworthy**, and run the "is this news or someone explaining?" anchor test.

---

## 4. The pipeline, step by step

```
 ① Topic pick        ← Event DB + topic score ≥ 12/15          [you: 2 min]
 ② Research brief    ← agent team, every claim cited             [you: 10–15 min fact check = Gate G2]
 ③ Scene plan+script ← Storyteller (Hindi) + Editor + Compliance [automatic]
 ④ Voice             ← ElevenLabs, your cloned voice             [automatic]
 ⑤ Avatar clips      ← HeyGen, only for AVATAR scenes            [automatic]
 ⑥ Visuals           ← charts from our DB, document "receipts",
                       animations, maps, stock B-roll             [automatic]
 ⑦ Assembly          ← Remotion: 16:9 long video + 9:16 Shorts   [automatic]
 ⑧ Auto QA           ← label present, loudness, numbers match
                       brief, banned phrases, duration            [automatic]
 ⑨ Final approval    ← you watch at 1.5× speed                   [you: 10–20 min = Gate G3]
 ⑩ Packaging         ← 3 titles, 3 thumbnails, description with
                       sources, chapters                           [you: 2 min to pick]
 ⑪ Publish           ← YouTube API (scheduled, AI disclosure on),
                       Instagram Reels, WhatsApp/newsletter post  [automatic]
 ⑫ Learn             ← retention & CTR pulled back into the
                       Event DB and topic scorer                  [automatic]
```

### 4a. The scene plan (the heart of the automation)

The Storyteller doesn't just write a script; it writes a **scene plan**, a structured list where each line of narration has its visual:

```yaml
video_id: FLG-2026-10-02-petrol
language: hi
format: flagship_16x9
scenes:
  - id: s1
    visual: AVATAR            # your twin on screen
    look: desk
    text: "पिछली बार जब आपने petrol भरवाया था… क्या meter पर दाम देखा था? [beat]"
  - id: s2
    visual: CHART
    chart: {type: line, series: [brent_inr, petrol_delhi_retail], period: "[VERIFY]"}
    text: "Crude सस्ता हुआ… पर pump पर दाम लगभग वहीं का वहीं है।"
  - id: s3
    visual: DOC_RECEIPT       # official document with highlighted line
    doc: {source: PPAC, doc_id: "...", page: 2, highlight: "price build-up table"}
    text: "पहले हम आपको एक litre petrol का पूरा हिसाब दिखाते हैं…"
  - id: s4
    visual: ANIMATION
    template: toll_plaza_analogy
    text: "ये tax बिल्कुल toll plaza की तरह काम करता है…"
  - id: s5
    visual: AVATAR
    look: standing
    text: "आपके petrol का दाम oil market तय नहीं करता। [beat] Budget तय करता है।"
shorts:
  - {from: s1, to: s2, hook_text: "Crude सस्ता, Petrol क्यों नहीं?"}
  - {from: s4, to: s5, hook_text: "Petrol पर लगता है 'toll tax'?"}
disclosure: {label: "AI-generated video · Research: [Name]", sebi_ra: null}
sources: [...]
```

Visual types: `AVATAR`, `CHART`, `DOC_RECEIPT`, `ANIMATION` (reusable templates: money flow, toll plaza, supply chain, timeline), `MAP`, `TEXT_CARD`, `BROLL`.

**Where the document "receipts" come from:** the Fact Extractor already cites the exact page of each source document. The renderer uses that page to show the real PDF page with the line highlighted. So every receipt on screen is tied to the fact it supports.

### 4b. Voice step details
- `[beat]` markers in the script become short pauses. Pace stays calm, per the Hindi guide.
- A **pronunciation dictionary** keeps English terms right (SEBI, NIFTY, repo, crore…).
- Regenerate any scene where the delivery sounds like a newsreader. The Editor flags long flat stretches.

### 4c. Avatar step details
- Send the **finished audio** to the avatar tool, so lip-sync matches the cloned voice exactly and we pay only for avatar minutes.
- Two looks, alternated by scene, avoid visual sameness.

### 4d. Automatic QA (before you see it)

| Check | Pass condition |
|---|---|
| AI disclosure label | Visible for the **entire** video (IT Rules 2026) |
| Numbers | Every number on screen and in narration matches the approved brief |
| Language | No banned anchor phrases; ≤ 1 spoken number per sentence |
| Compliance tier | No recommendation language unless the RA-approved flag is set |
| Audio | Loudness normalized (about −14 LUFS for YouTube); no clipping or silence gaps |
| Visual | No black frames, no overlapping text, captions in safe area |
| Receipts | Every `DOC_RECEIPT` points to an archived source with a valid page |

---

## 5. Output per topic (one pipeline run)

| Output | Format | Notes |
|---|---|---|
| Flagship or Pre-Market Desk | 16:9, Hindi primary | English audio track via YouTube's multi-language/auto-dubbing (check Hindi→English support) |
| 3–5 Shorts / Reels | 9:16, burned-in Hindi captions | Cut from the scene plan's `shorts` section |
| Thumbnails ×3 | Your twin's still frame + 2–4 words | Load into YouTube Test & Compare (a manual step in Studio) |
| Description | Hinglish summary, chapters, **sources list**, AI disclosure line | Generated from the scene plan |
| WhatsApp / newsletter card | Text + one chart | Auto-posted after publishing |

---

## 6. Safeguards that must stay on (even when fully automated)

| Safeguard | Why it's non-negotiable |
|---|---|
| **Your approval at G2 (facts) and G3 (final video)** | You're legally responsible for anything your twin says. Once you're a SEBI RA, you also sign off company-specific views and disclose AI use to clients |
| **`containsSyntheticMedia = true` on every upload + a continuous on-screen label** | YouTube policy + India's IT Rules 2026 |
| **Original research in every video; vary structures** | YouTube demonetizes generic, repetitive, template-based AI content, and can remove a whole channel from the Partner Program |
| **No volume spam** | Quality over quantity: 2–3 long videos + 3 desks a week, not 5 uploads a day |
| **Protect the twin** | 2-factor login on HeyGen, ElevenLabs, YouTube and Google; enroll in YouTube likeness detection; pin a public "we never DM you for money or tips" notice. Once you're popular, scammers will clone your face |
| **No other real person's face or voice** | Impersonation takedown risk (2–3 hours under the IT Rules) |

**Optional trust boosters (not required):** one real live Q&A a quarter, or a short real recorded message on channel milestones. Audiences trust an AI twin more when they occasionally see the real person.

---

## 7. Build order

| Step | Weeks | Result |
|---|---|---|
| **A. Twin + tool test** | 1–2 | Twin recorded; blind test of 2–3 voice/avatar combos; winner chosen |
| **B. Semi-automatic** | 3–6 | Script + voice + visuals automated. Avatar clips generated in the avatar tool's web app from our audio (a ~5-minute manual step). Assembly templates built in Remotion |
| **C. Fully automatic** | 7–12 | Avatar via API, auto QA, YouTube/Instagram API publishing, analytics loop |
| **D. Optimize** | later | Cheaper avatar options (open-source lip-sync on a rented GPU) if avatar minutes become the biggest cost |

---

## 8. Cost of the video layer (monthly)

| Item | Semi-automatic (steps A–B) | Fully automatic (step C) |
|---|---|---|
| ElevenLabs Creator (professional voice clone) | $22 | $22 (a higher tier if more characters are needed) |
| HeyGen | Creator, $29: ~600 credits ≈ 30 min of Avatar IV video | API access / higher tier: roughly $99+ depending on plan and credits (confirm current API pricing) |
| Remotion | Free (team ≤ 3 people) | Free (team ≤ 3 people) |
| Rendering | Founder's laptop or the existing VPS | A bigger VPS for rendering, ~$20–40 |
| Stock footage, music, YouTube/Instagram APIs | Free | Free |
| **Total video layer** | **≈ $51 (~₹4,500)** | **≈ $140–170 (~₹12,000–15,000)** |

**Avatar-minute check:** 1 flagship (18 min) + 2 desks (8 min) a week ≈ 34 min/week ≈ 140 min/month of video. At ~20% avatar share that's **~28 avatar minutes/month**, which fits the Creator plan's ~30 minutes. More videos, or more avatar time, means a higher tier.

### 8b. Cost at our target volume: 1 Reel a day + 8–10 long videos a month

**Volume:**
- 30 Reels × ~50 s ≈ **25 min**
- 8–10 long videos × 12–15 min ≈ **96–150 min**
- **Total ≈ 120–175 minutes of finished video a month**

**What HeyGen charges (Sep 2026; confirm on the pricing page before buying):**

| Item | Price |
|---|---|
| Creator plan | $29/month for 600 credits |
| Pro plan | from $49/month for 1,000 credits, with higher credit tiers available (≈ $0.045–0.05 per credit) |
| Avatar IV/V (realistic, our choice) | **20 credits per minute** (≈ $1/min on Pro) |
| Avatar III (older, less realistic) | ~3 credits per minute |
| API (for full automation) | Billed separately at roughly **$1–4 per generated minute** depending on the avatar engine. **Much more expensive than web-plan credits** |
| Unused monthly credits | Roll over for one more month |

**Avatar minutes needed, by how much of the video shows your face:**

| Face on screen | Avatar minutes / month | HeyGen credits | HeyGen via web app | HeyGen via API (~$4/min) |
|---|---|---|---|---|
| **Recommended:** ~20% of long videos, ~40% of Reels (hook + close) | ~29–40 min | ~580–800 | **Pro $49 (1,000 credits) ≈ ₹4,300** | ~$116–160 ≈ ₹10,000–14,000 |
| Lean: ~15% of long videos, ~30% of Reels | ~22–30 min | ~440–600 | **Creator $29 ≈ ₹2,550** (tight) | ~$88–120 ≈ ₹7,700–10,500 |
| Face for the whole runtime | ~120–175 min | ~2,400–3,500 | ~$115–175 ≈ ₹10,000–15,500 (higher Pro tier) | ~$480–700 ≈ ₹42,000–62,000 |

**Voice (ElevenLabs) at this volume:** we narrate the **whole** runtime, not just the face parts.
- Roughly 1,000 credits ≈ 1 minute of speech, so 120–175 min plus ~20% for re-takes ≈ **145–210k credits a month**.
- The Creator plan ($22) includes ~121k credits, which is **not enough at full volume**.
- Plan for **Pro ($99 ≈ ₹8,700, ~600k credits)**, or Creator plus overage. Check the current overage rates.

**Video-layer total at target volume:**

| Setup | Monthly (approx.) |
|---|---|
| **Recommended face mix, avatar clips generated in HeyGen's web app** (a ~5-minute manual click per video) | **HeyGen Pro $49 + ElevenLabs Pro $99 ≈ $148 ≈ ₹13,000** |
| Lean face mix, web app | HeyGen Creator $29 + ElevenLabs Pro $99 ≈ $128 ≈ ₹11,300 |
| Recommended face mix, **fully automatic via API** | ≈ $215–260 ≈ ₹19,000–23,000 |
| Face for the whole runtime, web app | ≈ $215–275 ≈ ₹19,000–24,000 |
| Face for the whole runtime, via API | ≈ $580–800 ≈ ₹51,000–70,000 |

**Recommendation:** keep the **avatar step semi-automatic** (generate the clips in HeyGen's web app from our finished audio, ~5 minutes per video) until revenue justifies API pricing. Everything else stays automatic. Also ask HeyGen whether web-plan credits can be used through the API. If they can, full automation costs about the same as the web app.

**Ramp-up:** in months 1–2 (fewer long videos while we test), HeyGen Creator + ElevenLabs Creator ≈ $51 (≈ ₹4,500) is enough.

---

## Sources

- [HeyGen pricing](https://www.heygen.com/pricing) · [HeyGen API pricing explained](https://help.heygen.com/en/articles/10060327-heygen-api-pricing-explained) · [eesel: HeyGen pricing 2026 (credits, Avatar IV)](https://www.eesel.ai/blog/heygen-pricing)
- [HeyGen: create a digital twin](https://www.heygen.com/academy/avatars/how-to-create-a-digital-twin) · [HeyGen: recording your consent video](https://help.heygen.com/en/articles/12092609-recording-your-consent-video) · [HeyGen developer docs: avatar consent](https://developers.heygen.com/docs/avatar-consent) · [MindStudio: footage requirements](https://www.mindstudio.ai/blog/what-is-heygen-avatar-v-digital-twin-explained)
- [ElevenLabs: professional voice cloning](https://elevenlabs.io/docs/eleven-creative/voices/voice-cloning/professional-voice-cloning) · [ElevenLabs pricing](https://elevenlabs.io/pricing)
- [Remotion license & pricing](https://www.remotion.dev/docs/license/pricing)
- [YouTube Data API revision history (`containsSyntheticMedia`, Oct 2024)](https://developers.google.com/youtube/v3/revision_history) · [YouTube Help: "How this content was made" disclosures](https://support.google.com/youtube/answer/15447836?hl=en)
- [Phyllo: Instagram Reels API guide 2026](https://www.getphyllo.com/post/a-complete-guide-to-the-instagram-reels-api)
- YouTube Jul 2026 inauthentic-content policy and India's IT Rules 2026: see [`strategy-research-2026-09.md`](strategy-research-2026-09.md)
