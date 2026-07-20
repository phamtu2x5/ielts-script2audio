# Voice inventory deep-dive (open-weight focus)

**Date:** 2026-07-20  
**Purpose:** Agent-readable research notes so future sessions do not re-discover voice constraints.  
**Human owner:** education product, **no fees**; license is **lower priority** than inventory/accent fit (still record facts).  
**Benchmark / notebook:** not built yet — this doc is desk research only (`NOT_EXECUTED` audio).  
**Script policy:** never silent-edit transcript; report issues to owner.

## 1. Why inventory matters more than “model sounds nice”

IELTS Listening Parts force **hard speaker counts**:

| Part | Content speakers required | Failure mode if inventory weak |
|------|---------------------------|--------------------------------|
| 1 | exactly 2 | Same voice for both roles → unusable dialogue |
| 2 | exactly 1 | Need stable long monologue, not multi-clone chaos |
| 3 | 2–4 | **Hardest**: listeners must tell speakers apart without transcript |
| 4 | exactly 1 | Academic mono stability |

If we pick a model that only “clones from a sample” but we have no controlled sample bank, we will discover the gap **after** Colab integration — the failure mode the owner wants to avoid.

## 2. Two inventory types (definitions for agents)

### Type F — Fixed voice IDs

- Model ships a **closed list** of named voices (e.g. `bf_emma`).
- Countable offline: “we have 8 British voices”.
- Pipeline mapping: `voice_profile_id` → `backend_voice_id` is a static table.
- Accent often encoded in ID or `lang_code`.
- **Example in this research:** Kokoro-82M.

### Type Z — Zero-shot / reference-audio inventory

- Model does **not** ship “Speaker A/B/C” catalog like Azure.
- Each logical speaker needs a **reference clip** (and usually reference transcript).
- “We have 4 Part 3 speakers” means **we prepared 4 refs**, not “model has 4 built-ins”.
- Accent = accent **of the reference**, not a `en-GB` dropdown (unless an instruct dialect API exists).
- **Examples:** F5-TTS (ref-only); CosyVoice primary path zero-shot (+ optional SFT mode without public English speaker list found).

### Type H — Hybrid

- Fixed SFT speakers **plus** zero-shot.  
- CosyVoice advertises SFT model variant, but **no public enumerated English SFT speaker list** was found in desk pass — treat English multi-cast as **Type Z until proven Type F**.

## 3. Project mapping rule (ADR-0002)

```text
Control plane:  voice_profile_id  (abstract, e.g. vp_spk_a)
Adapter/Colab:  backend_voice_id OR (ref_wav_path + ref_text)
```

Domain core must not embed vendor voice names. Inventory research decides **what the adapter table looks like**.

## 4. Kokoro-82M — inventory (Type F) — HIGH CONFIDENCE desk

**Sources:** [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) VOICES.md (via HF); [hexgrad/kokoro](https://github.com/hexgrad/kokoro).

### 4.1 Scale & mechanism

- ~82M params; `voice='af_heart'` style API; `lang_code` must match voice family.
- Total marketed: **54 voices / 8 languages** (v1.0 messaging).

### 4.2 English inventory (critical for IELTS)

**American English** (`lang_code='a'`): **11 female (`af_*`) + 9 male (`am_*`) = 20 voices**

Female examples: `af_heart` (grade A), `af_bella` (A-), `af_nicole` (B-), …  
Male examples: `am_adam`, `am_michael`, `am_fenrir`, …

**British English** (`lang_code='b'`): **4 female (`bf_*`) + 4 male (`bm_*`) = 8 voices**

| ID | Grade (training-data quality estimate from VOICES.md) |
|----|------------------------------------------------------|
| bf_alice | D |
| bf_emma | B- |
| bf_isabella | C |
| bf_lily | D |
| bm_daniel | D |
| bm_fable | C |
| bm_george | C |
| bm_lewis | D+ |

Grades A–F estimate data quality/quantity (A best). Many lower grades → **lab listening required**; do not assume all 8 GB voices are production-equal.

### 4.3 Fit to IELTS speaker constraints

| Need | Kokoro desk fit |
|------|-----------------|
| Part 1 (2 speakers) | **Yes** — pick 2 distinct EN or GB IDs (timbre/gender) |
| Part 2 / 4 (1 speaker) | **Yes** — single ID throughout |
| Part 3 (3–4 speakers) | **Yes on paper for EN-US** (20 voices). **For en-GB: 8 voices** → 3–4 distinct is **possible** but quality grades vary; must lab confusability |
| Narrator later | Possible 5th ID if delivery_profile expands |
| en-GB preference | **Native lang_code `b` + bf_/bm_** — best fixed-GB open-weight option in this shortlist |
| Re-render consistency | Same `voice` id → expected stable (lab confirm) |
| Answer codes | No rich SSML; rely on Stage-2 `spoken_text` |

### 4.4 Gaps

- Full multi-lang list beyond EN less relevant.
- Naturalness of lower-grade GB voices unknown without lab.
- Not billion-param class — still **best inventory clarity**.

### 4.5 License (light)

Apache-2.0 claim on project materials — education/no-fee use likely fine; re-verify at pilot.

---

## 5. CosyVoice 2 / Fun-CosyVoice 3 — inventory (Type Z primary) — MEDIUM CONFIDENCE

**Sources:** [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice).

### 5.1 Scale & modes

| Model | Size |
|-------|------|
| CosyVoice-300M / SFT / Instruct | 300M |
| CosyVoice2-0.5B | 0.5B |
| Fun-CosyVoice3-0.5B | 0.5B |

Modes called out: **zero_shot**, **cross_lingual**, **sft**, **instruct** (language/dialect/emotion/speed/volume — dialect detail strongest for **Chinese**).

### 5.2 Built-in speaker list?

**Desk result: NO public enumerated English SFT speaker ID list found** (no “spk_0 = British male …” table in README scrape).

Implications:

- Do **not** plan adapter as static `vp_* → english_speaker_03` until SFT list is extracted from actual checkpoint/code on Colab.
- Default planning assumption: **each IELTS content speaker needs a reference wav** (zero-shot).

### 5.3 English / British

- English is one of **9 languages** supported.
- **18+ Chinese dialects** highlighted; **British English not specifically documented**.
- en-GB strategy = **supply British-accent reference clips** (or hope SFT presets include EN — unproven).

### 5.4 Multi-speaker dialogue

- No dedicated “multi-party dialogue session” API found.
- Pattern: **per-utterance / per-segment synthesis** with speaker-specific ref or SFT id — aligns with our segment pipeline.

### 5.5 Fit to IELTS

| Need | CosyVoice desk fit |
|------|--------------------|
| Part 1 (2) | **Yes if 2 refs** (or 2 SFT ids if exist) |
| Part 3 (3–4) | **Yes only with 3–4 controlled refs** + listening test for confusability |
| en-GB | **Not guaranteed by catalog** — ref-dependent |
| Long mono Part 4 | Size 0.5B attractive; stability **lab** |
| Re-render | Must pin **same ref** (or id) per `voice_profile_id` |
| Pronunciation | Mentions English CMU phoneme inpainting — secondary; still use `spoken_text` |

### 5.6 Project cost of Type Z (important)

If CosyVoice is primary, project must add **Voice Bank workstream**:

1. Collect/create 4–6 short clean refs (consent if human).  
2. Store paths in Colab-accessible inventory YAML (not in domain core).  
3. Map `vp_spk_a` → `ref_a.wav` + `ref_a.txt`.  
4. QA: same ref across all segments of one Part.

Without this, model choice **fails inventory constraint** even if quality is high.

### 5.7 License (light)

Repo Apache-2.0 — education use likely OK; re-verify weights cards at download time.

---

## 6. F5-TTS — inventory (Type Z only) — HIGH CONFIDENCE on mechanism

**Sources:** [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS).

### 6.1 Mechanism

- **No fixed voice list.**
- Inference: `--ref_audio` + `--ref_text` + `--gen_text`.
- Multi-speaker example config: multi-style/multi-speaker Gradio + `story.toml` multi-voice example.
- English via Emilia ZH–EN training.

### 6.2 Fit to IELTS

| Need | F5-TTS desk fit |
|------|-----------------|
| Any Part multi-speaker | **Only via N reference clips** |
| en-GB | **Only if ref is GB** |
| Re-render | Same ref required |
| Fixed casting without assets | **Fail** |

### 6.3 License (light; education no-fee)

- Code MIT; pretrained **CC-BY-NC** (Emilia).  
- Owner product is **education, no fees** — NC often still needs careful reading (NC ≠ “any free education always OK” in all jurisdictions/interpretations).  
- Flag for legal skim later; **not blocking lab** for private education experiments, but do not ignore forever.

---

## 7. Comparative decision matrix (inventory-first)

| Criterion | Kokoro | CosyVoice 2/3 | F5-TTS |
|-----------|--------|---------------|--------|
| Inventory type | **F fixed IDs** | Z (+ SFT unlisted EN) | **Z only** |
| Countable EN-US voices | **20** | Unknown fixed | 0 fixed |
| Countable EN-GB voices | **8** | 0 documented | 0 fixed |
| Part 3 without building ref bank | **Possible** | **No** | **No** |
| en-GB without GB refs | **Possible** (bf_/bm_) | **No** | **No** |
| Model size vs Colab L4/A100 | Light | 0.3–0.5B OK | GPU Base OK |
| Risk of “integrate then missing voices” | **Low** | **High if skip voice bank** | **High if skip voice bank** |
| Naturalness ceiling (desk guess) | Medium | Higher potential | Higher potential |
| Education no-fee license worry | Low (Apache claim) | Low (Apache claim) | Medium (CC-BY-NC weights) |

## 8. Recommendation for *selection strategy* (not final_selected)

**Goal:** avoid late inventory failure.

### Primary recommendation for first serious lab path

1. **Kokoro as inventory-safe baseline (must lab)**  
   - Proves pipeline: manifest → voice_profile map → multi-speaker Part 1 & Part 3 with **known IDs**.  
   - Only open-weight candidate with **documented en-GB fixed inventory (8)**.  
   - If Part 3 confusable or GB quality poor → escalate to CosyVoice **with voice bank plan**, not instead of understanding inventory.

2. **CosyVoice as quality/scale candidate (lab only after voice-bank plan written)**  
   - Do not Colab-integrate as “default” until owner accepts Type Z workflow (4+ refs).  
   - Attractive 0.5B on L4/A100; English OK; GB not catalogued.

3. **F5-TTS**  
   - Same Type Z cost as CosyVoice; NC weights note; use if CosyVoice fails or for A/B quality — **not** first inventory fix.

4. **API models**  
   - Remain research-only (budget).

### Explicit non-recommendation

- Choosing CosyVoice/F5-TTS **only** because “bigger / newer” without Part 3 voice plan.  
- Assuming CosyVoice SFT has English presets without extracting list from checkpoint.  
- Building Colab notebook before this inventory logic is accepted (owner: research first).

## 9. Minimum voice bank if Type Z is chosen later

For full test production later:

| Role | Min refs | Notes |
|------|----------|-------|
| Content A | 1 | Clean 5–15s, neutral, matching accent target |
| Content B | 1 | Clearly different timbre from A |
| Content C/D (Part 3) | 1 each | Timbre/formality separation |
| Narrator (optional) | 1 | Distinct from content |

Store outside domain package; adapter reads inventory YAML.

## 10. Evidence still missing (before final model pick)

- [ ] Human listen Kokoro GB set (`bf_*`/`bm_*`) for intelligibility + Part 3 confusion  
- [ ] On Colab: dump CosyVoice SFT speaker list from actual weights/code if any  
- [ ] Measure CosyVoice/F5 zero-shot with **project-owned** refs (not random web voices)  
- [ ] Long-form Part 4 stability comparison  
- [ ] Codes (postcode/spelling) with Stage-2 `spoken_text`  
- [ ] Optional legal skim F5-TTS NC for education no-fee  

## 11. Agent checklist (future sessions)

```text
IF proposing TTS model:
  1. Classify Type F / Z / H
  2. Count fixed EN + GB voices OR require voice-bank size
  3. Map to Part 1–4 constraints explicitly
  4. State en-GB strategy
  5. Do not claim final_selected without lab
  6. Never edit transcript script silently
```
