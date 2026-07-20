# Extra candidates + fixed-voice survey (desk)

**Date:** 2026-07-20  
**Focus:** Qwen3-TTS 1.7B Base, Fish Audio S2 Pro, Chatterbox Multilingual V; plus other **fixed voice ID** options like Kokoro.  
**Owner priority:** Fixed voice IDs first (no stable voice bank yet). Education, no fees. Colab L4/A100. API research-only.  
**Audio lab:** `NOT_EXECUTED`.  
**Script policy:** never silent-edit transcript.

## 1. User-named models

### 1.1 Qwen3-TTS 1.7B **Base**

| Field | Desk finding |
|-------|----------------|
| Source | [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS), HF `Qwen/Qwen3-TTS-12Hz-1.7B-Base` |
| Size | **1.7B** (also 0.6B variants) — fits “large model on Colab” interest |
| License | **Apache-2.0** (desk) |
| **Inventory type** | **Type Z (clone)** for **Base** — needs ~3s `ref_audio` (+ optional `ref_text`) |
| Fixed voice bank on **Base**? | **No** |
| English | Yes (10 languages family) |
| British preset | **Not** on Base; accent follows reference |
| SSML / lexicon | Not documented as Azure-style SSML/lexicon |
| Multi-speaker | Multiple speakers = **multiple clone prompts** / refs; batch APIs exist |
| Relation to fixed voices | Sibling model **CustomVoice** (1.7B/0.6B) has **9 named timbres**, not Base |

**CustomVoice fixed list (9) — important distinction:**

| Speaker id | Notes (desk) |
|------------|----------------|
| Vivian, Serena | (non-EN native focus in blurbs) |
| Uncle_Fu, Dylan, Eric | Chinese regional notes |
| **Ryan**, **Aiden** | **English** — described as American-style male sunny voices |
| Ono_Anna | Japanese |
| Sohee | Korean |

→ For **fixed IDs**, evaluate **Qwen3-TTS CustomVoice**, **not** “1.7B Base”.  
→ Base alone **does not** solve “no voice bank” constraint.  
→ Even CustomVoice: only **~2 English-named** speakers in the 9 → **Part 3 with 3–4 distinct EN speakers is weak** unless cloning or non-native speaker ids used cross-lingually (quality risk).

**IELTS fit (Base):** Part multi-speaker only with refs → same class as CosyVoice/F5 for inventory.  
**IELTS fit (CustomVoice):** Fixed IDs exist but **EN inventory too small** for Part 3 (3–4) without stretching.

### 1.2 Fish Audio S2 Pro

| Field | Desk finding |
|-------|----------------|
| Status | **Primarily product/API** positioning in public materials; “S2 Pro” not confirmed as fully open fixed-voice OSS stack equivalent to Kokoro |
| Related open line | Fish ecosystem / OpenAudio S1-class open weights appear in community (e.g. OpenAudio-S1-mini) — **verify exact checkpoint names at lab time** |
| Inventory | Product side emphasizes **voice clone / library on platform**, not a small open `bf_emma`-style ID table for offline Colab |
| Constraint fit | **Weak for “fixed IDs, no voice bank, Colab open-weight”** unless a specific open release with preset speakers is pinned later |
| Label | `research_only` until a concrete open-weight + voice-ID artifact is identified |

Do **not** shortlist S2 Pro as Kokoro-class fixed inventory without a verifiable open speaker list + local/Colab weights path.

### 1.3 Chatterbox Multilingual (ResembleAI) — “V” / V3 class

| Field | Desk finding |
|-------|----------------|
| Source | [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) |
| Size | Multilingual ~**500M** class (V3 path) |
| License | **MIT** (repo badge/docs desk) |
| Inventory type | **Type Z** — `audio_prompt_path` reference; **no fixed built-in voice list** |
| English | `en` among 23+ languages |
| British fixed | **No** separate en-GB voice bank documented |
| Multi-speaker | Different refs per speaker |
| SSML/lexicon | Not the selling point; clone-first |
| Label | Same inventory class as CosyVoice/F5 — **not** preferred while owner has no voice bank |

## 2. Fixed-voice (Type F) survey beyond Kokoro

### 2.1 Kokoro-82M (reference baseline) — best Type F clarity so far

- **20** American (`af_*`/`am_*`) + **8** British (`bf_*`/`bm_*`) named voices.  
- See `voice-inventory-deep-dive.md`.

### 2.2 MeloTTS — Type F **accents**, thin multi-cast

| Field | Desk finding |
|-------|----------------|
| Source | [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS) |
| License | **MIT** |
| English “voices” | **Accent packs**: EN-US, **EN-BR**, EN-AU, EN-India, EN-Default — not a large cast of distinct character IDs |
| Multi-speaker for Part 3 | **Weak**: switching accent ≠ 3–4 distinct people in one Part; typically **one speaker persona per language/accent model** |
| Role | Possible **single-speaker** Part 2/4 EN-BR smoke; **not** Part 3 cast solution |
| Label | Optional niche; **not** Kokoro replacement for multi-speaker |

### 2.3 Qwen3-TTS **CustomVoice** — Type F but small EN set

- **9** named speakers total; **~2 English** (Ryan, Aiden, American-leaning).  
- Better than Base for “no ref file”, **insufficient** for Part 3 four-way EN without hacks.  
- Label: `shortlist_lab` only for **2-speaker Part 1 experiments** if desired; **not** full-test casting.

### 2.4 Piper (ONNX) — Type F many files

- Many community voices as separate ONNX; countable inventory **per downloaded voice**.  
- en-GB voices exist in ecosystem but **quality uneven**; manage as file inventory.  
- Label: optional baseline (already known).

### 2.5 Not Type F (do not confuse with fixed bank)

| Model | Type | Why not “Kokoro-like bank” |
|-------|------|----------------------------|
| Qwen3-TTS **Base** 1.7B | Z | Clone only |
| CosyVoice 2/3 | Z (+ SFT unlisted EN) | No public EN ID bank found |
| F5-TTS | Z | Ref only |
| Chatterbox Multilingual | Z | Ref only |
| Fish S2 Pro (product) | Platform/clone | Not verified open fixed IDs for Colab |

## 3. Decision impact (inventory-first, no voice bank)

| Need | Best desk match |
|------|-----------------|
| Fixed IDs + multi EN/GB cast | **Kokoro** still strongest documented |
| Large param (1.7B) without voice bank | **Qwen Base / Chatterbox** do **not** remove voice-bank need |
| Fixed IDs + large param | **Qwen CustomVoice** only partial (2 EN) — gap for Part 3 |
| EN-BR single speaker | MeloTTS EN-BR or Kokoro `bf_*`/`bm_*` |
| Avoid late “missing voices” | Do **not** pick Base/Chatterbox/Fish-product as primary cast engine without bank |

## 4. Updated shortlist stance (provisional)

1. **Primary inventory path:** Kokoro (lab first).  
2. **Watch Type F large:** Qwen **CustomVoice** only for limited 2-speaker tests — document EN count gap.  
3. **Type Z large (Qwen Base 1.7B, CosyVoice, F5, Chatterbox):** only after voice bank **or** explicit decision to build one.  
4. **Fish S2 Pro:** research-only until open fixed-voice artifact is clear.  
5. **MeloTTS:** optional mono EN-BR; not Part 3 cast.  
6. Final backend: still **`not_selected`**.

## 5. Sources

- [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)  
- [Qwen/Qwen3-TTS-12Hz-1.7B-Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base)  
- [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)  
- [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS)  
- Kokoro VOICES.md / HF Kokoro-82M  
- Fish / OpenAudio: product + community open lines — re-pin exact URLs at lab time  
