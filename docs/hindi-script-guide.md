# Finmedia — Hindi-First Script Guide (हिंदी + English terms)

*Decision (26 Sep 2026): **our primary language is Hindi, with English financial terms used naturally** (the way people actually talk about money in India). English becomes a secondary audio track. This guide is the rulebook for writers, voice artists and the AI script pipeline. Companion to [`voice-and-style-guide.md`](voice-and-style-guide.md).*

---

## 1. Why Hindi-first

- **Reach.** Most of our target audience (young investors, F&O traders, first-salary earners) understands Hindi best. If a viewer feels they're "not fully getting it" in English, they leave, and the video dies. Understanding comes before everything else.
- **Trust.** A calm, clear Hindi explanation of a SEBI study feels like a knowledgeable elder sibling. The same thing in formal English can feel distant.
- **The ad-rate trade-off is manageable.** Hindi ad rates are lower than English, but:
  1. we add an **English audio track** to the same video (YouTube's multi-language audio), which recovers part of the English audience;
  2. ads were never our core revenue. Subscriptions, B2B and tools are.
- **Differentiation.** Hindi finance YouTube is dominated by loud tip-style content. **Calm, researched Hindi is rare.** That's our space.

---

## 2. The register: "घर वाली हिंदी, पर शांत"

We speak the way an educated Indian explains money at the dinner table: Hindi sentences with English terms, calm and respectful.

| ✅ Do | ❌ Don't |
|---|---|
| Use **"आप"** for the viewer, always | "तुम," "भाई लोग," "दोस्तों" every other line |
| Use **"हम"** for the channel ("हमने data देखा," "हम दिखाते हैं") | Mixing "मैं" and gendered verbs (दिखाता/दिखाती). "हम" is gender-neutral and matches our "we investigate" brand |
| Short sentences, one idea each | Long sarkari sentences |
| Everyday Hindi for feelings and logic: नुकसान, मुनाफ़ा, हिसाब, वजह, असर, सच, ख़तरा, मौका | Shuddh or official Hindi: प्रतिभूति, मौद्रिक नीति, राजकोषीय घाटा, अंतर्निहित |
| English for terms people already use (SIP, EMI, market, F&O) | Forcing Hindi translations nobody uses ("व्यवस्थित निवेश योजना" for SIP) |
| A calm, steady voice | The shouting Telegram-tips register ("रॉकेट," "पैसा डबल," "jackpot") |

---

## 3. Word glossary

### 3a. Keep in English (the audience already thinks in these)
market · share / stock · SIP · mutual fund · EMI · loan · F&O · options · expiry · trader · investor · portfolio · return · IPO · RBI · SEBI · repo rate · inflation · GDP · budget · tax · GST · crude oil · refinery · margin · algo trading · AI · data · backtest · chart · level · trend · fund · company · regulator · circular · document · record · dollar · report

### 3b. Say in Hindi (warmer, clearer)
नुकसान (loss) · मुनाफ़ा (profit) · कमाई (earnings) · कर्ज़ (debt) · ख़र्च (cost) · बचत (savings) · हिसाब (calculation) · सवाल (question) · वजह (reason) · असर (impact) · सच / असली कहानी (the real story) · ख़तरा (risk) · मौका (opportunity) · सोना (gold) · महंगाई (inflation, used alongside the English word) · ब्याज (interest) · दाम (price) · उतार-चढ़ाव (volatility)

### 3c. Explain once, then use
| Term | One-line Hindi explanation (first use) |
|---|---|
| repo rate | "वो ब्याज दर जिस पर RBI बैंकों को पैसा देता है, और यहीं से आपकी EMI तय होनी शुरू होती है।" |
| real return | "महंगाई घटाने के बाद जो असली return बचता है।" |
| crack spread | Say "refinery margin": "crude और petrol-diesel के दाम के बीच का फ़र्क़, जो refinery कमाती है।" |
| algo trading | "जब trade इंसान नहीं, computer के बनाए rules से होते हैं।" |
| tokenization | "किसी asset को digital हिस्सों में बाँटना, ताकि उसे blockchain जैसे system पर ख़रीदा-बेचा जा सके।" |
| consultation paper | "Regulator का proposal. अभी final rule नहीं है।" (Always say this!) |

### 3d. Avoid entirely in speech
"basis points" (say "0.25 percent"), "dot plot" (say "Fed का अपना अनुमान"), "million/billion" (see numbers), and stacks of technical-analysis jargon ("bullish engulfing," "bull flag"). If it's needed, put it on screen, not in the voice.

---

## 4. Numbers

- **Indian number system only:** हज़ार, लाख, करोड़. Never say "million" or "billion" in the Hindi voice.
- **Convert foreign amounts:** "$2.8 billion, यानी लगभग [VERIFY: ₹ amount at current rate] करोड़ रुपये."
- **Percent:** say "percent" (the younger audience says it naturally); show "%" on screen.
- **Dates:** "23 सितंबर," "financial year 2024." Say the year naturally ("दो हज़ार चौबीस").
- **One spoken number per sentence**, and at most three in any 20 seconds. The screen carries the rest (from the 100k playbook).
- Round in speech, stay exact on screen: say "लगभग 61 हज़ार करोड़" while the screen shows the exact SEBI figure with its source.

---

## 5. Writing and recording format

- **Script in Devanagari, with English terms written in Roman letters** (for example: "SEBI की report कहती है…"). The voice artist or TTS then says English words the English way.
  - Some Hindi TTS voices mispronounce Roman words. **Test the chosen voice with 20 sample lines** before locking the convention. If it fails, write the English terms in Devanagari (मार्केट, रिपोर्ट).
- **Pace:** calm, about 10–15% slower than normal conversation. Mark pauses `[beat]` before key numbers and reveals.
- **Captions:** Hindi (Devanagari) as the primary captions, plus English subtitles.
- **Audio tracks:** Hindi primary. **English secondary track** (AI-dubbed and disclosed for the daily desk; a human voice for big flagships). Tamil and Telugu tracks later for the top videos.

---

## 6. Titles, thumbnails, descriptions

People in India often search Hindi topics in **Roman-script Hinglish** ("petrol price kyun nahi ghata"), and sometimes in Devanagari. We don't guess; we test.

- **Use YouTube Test & Compare with 3 title variants** on every flagship:
  1. Hinglish in Roman script: *"Crude Sasta Hua, Petrol Kyun Nahi? | Poora Hisaab"*
  2. Hindi in Devanagari: *"Crude सस्ता हुआ, Petrol क्यों नहीं? पूरा हिसाब"*
  3. English: *"Crude Fell. Why Didn't Your Petrol Get Cheaper?"*
  After 10–15 videos, the data tells us our default.
- **Thumbnail text:** 2–4 words, large; test Devanagari against Roman. Devanagari stands out in a feed full of English thumbnails.
- **Description:** first 2 lines in Hinglish with the main search phrase, then a short English summary, then the sources list (our "receipts").
- **Real statistics in titles still apply:** *"91% Traders ka Paisa Dooba — Kahan Gaya? SEBI Data"* (the source is shown on screen in the first 60 seconds).

---

## 7. Our 12 script moves, in Hindi

The toolkit from the [transcript teardown](transcript-teardown-100k-playbook.md), written in our register:

| # | Move | Hindi line pattern |
|---|---|---|
| 1 | Reversal hook | "सबने यही कहा… **फिर market ने कुछ ऐसा किया, जिसकी किसी ने उम्मीद नहीं की थी।**" |
| 2 | Three strange clues | "और इसकी वजह ___ से कम, और तीन चीज़ों से ज़्यादा जुड़ी है: ___, ___, और ___।" |
| 3 | Sequencing promise | "पहले हम आपको ये दिखाते हैं, क्योंकि इसे देखने के बाद बाकी पूरी कहानी समझ आ जाएगी।" |
| 4 | Headline vs. fine print | "ज़्यादातर लोग सिर्फ़ headline पढ़ते हैं। और headline इस कहानी का सबसे कम ज़रूरी हिस्सा है।" |
| 5 | Do the math | "चलिए, एक सीधा-सा हिसाब लगाते हैं।" |
| 6 | Catch the contradiction | "अब ये line पढ़िए… और फिर उन्हीं के अपने numbers देखिए।" |
| 7 | Plant a number | "ये number याद रखिए। Video के आख़िर में यही सबसे ज़रूरी होगा।" |
| 8 | Transferable skill | "अगर ये तीन बातें समझ गए, तो अगली बार ऐसा होने से पहले ही आप पहचान लेंगे।" |
| 9 | Raw vs. finished | "Crude सस्ता हुआ… पर petrol नहीं। क्योंकि problem तेल में नहीं, बीच की एक कड़ी में है।" |
| 10 | Self-debunk | "अब एक ईमानदार बात। जो हमने अभी दिखाया, उसके ख़िलाफ़ सबसे मज़बूत तर्क ये है।" |
| 11 | Thesis line | "आपके petrol का दाम oil market तय नहीं करता। Budget तय करता है।" |
| 12 | Watch list + "we're wrong if" | "अगले 90 दिनों में ये चार चीज़ें देखिए। और अगर ___ हुआ, तो हम ग़लत हैं।" |

---

## 8. Sample cold opens (Hindi-first)

### A. The Transfer
> Financial year 2024 में, India के आम traders ने F&O में, costs से पहले ही, **61 हज़ार करोड़ रुपये** से ज़्यादा गँवाए। [beat]
> उसी साल, बड़ी trading firms और foreign investors ने कमाए… [beat] लगभग उतने ही।
> और उस मुनाफ़े का लगभग पूरा हिस्सा… **machines** ने कमाया था।
> ये कहानी है Indian market के सबसे बड़े, और सबसे ख़ामोश transfer की, और उन जगहों की, जहाँ आम investor के पास आज भी edge है।

### B. IRDAI / PB Fintech
> 23 सितंबर की शाम। Market बंद हो चुका था। [beat]
> India के insurance regulator, IRDAI, ने एक document जारी किया। नाम इतना boring कि शायद ही किसी ने पढ़ा हो। [beat]
> अगले दिन दोपहर तक, India की सबसे जानी-मानी fintech companies में से एक का share **36 percent** तक गिर चुका था।
> ये कहानी एक company की नहीं है। ये कहानी इस सवाल की है: एक customer लाने का ख़र्च आख़िर कौन उठाता है… और जब regulator कह दे कि ये ख़र्च बहुत ज़्यादा है, तब क्या होता है?

### C. Crude सस्ता, Petrol क्यों नहीं? *(all [VERIFY] items must be confirmed from PPAC / oil company notices first)*
> पिछले [VERIFY: अवधि] में crude oil [VERIFY: %] सस्ता हुआ। [beat]
> हर headline ने यही कहा: अब petrol-diesel सस्ता होगा।
> नहीं हुआ। [beat] ज़्यादातर शहरों में, एक रुपया भी नहीं।
> और इसकी वजह तेल से कम, और तीन चीज़ों से ज़्यादा जुड़ी है: हर litre पर लगने वाला एक fixed tax, oil companies का [VERIFY: पुराने नुकसान की भरपाई वाला तर्क], और refinery का एक margin, जिसका नाम ज़्यादातर लोगों ने कभी सुना भी नहीं।
> पहले हम आपको एक litre petrol का पूरा हिसाब दिखाते हैं, क्योंकि इसे देखने के बाद बाकी पूरी video समझ आ जाएगी।

---

## 9. Pre-publish language checklist

- [ ] A 16-year-old in Lucknow and a 35-year-old in Pune would both follow every sentence
- [ ] "आप" for the viewer, "हम" for the channel, no gendered first-person verbs
- [ ] Every technical term used 3+ times is explained once in one Hindi line
- [ ] Indian numbering (लाख/करोड़); one spoken number per sentence
- [ ] "Proposal है, final rule नहीं" stated wherever it applies
- [ ] No shuddh/sarkari words; no Telegram-tips slang
- [ ] 3 title variants loaded in Test & Compare
- [ ] Hindi captions + English subtitles; English audio track added
- [ ] AI disclosure (if synthetic voice or avatar) visible for the whole video
