# Candidates: Parler-TTS Mini v1.1, Orpheus, MeloTTS, Voxtral-4B-TTS-2603

**Date:** 2026-07-20  
**Desk only** — audio lab `NOT_EXECUTED`.  
**Owner constraints:** prefer **fixed voice IDs**; no stable voice bank; Colab L4/A100; education no-fee; API research-only.  
**Script policy:** never silent-edit transcript.

Note: “Parler-TTS Mini v1.1O” treated as **Mini v1.1** (official HF id `parler-tts/parler-tts-mini-v1.1`).

---

## 1. Parler-TTS Mini v1.1

| Field | Desk finding |
|-------|----------------|
| Source | [parler-tts/parler-tts-mini-v1.1](https://huggingface.co/parler-tts/parler-tts-mini-v1.1), [huggingface/parler-tts](https://github.com/huggingface/parler-tts) |
| Size | Mini class ~**0.88B–0.94B** params (card/safetensors order) |
| License | **Apache-2.0** |
| Language | **English** focus |
| Control style | Natural-language **description** of voice (rate, noise, pitch…) **plus** optional **named speaker** in the description |
| Fixed speakers | Trained for consistency on **34 named speakers** |

### Named speaker list (official family docs)

Laura, Gary, Jon, Lea, Karen, Rick, Brenda, David, Eileen, Jordan, Mike, Yann, Joy, James, Eric, Lauren, Rose, Will, Jason, Aaron, Naomie, Alisa, Patrick, Jerry, Tina, Jenna, Bill, Tom, Carol, Barbara, Rebecca, Anna, Bruce, Emily.

Usage pattern (not `voice=id` SDK): put the name inside the description string, e.g.  
`Jon's voice is monotone yet slightly fast...`

### Inventory classification

- **Not** Kokoro-style pure `voice='bf_emma'`.  
- **Yes** countable cast if project **locks description templates** per `voice_profile_id` (pseudo Type F).  
- **en-GB:** official Mini list is **not** labeled British vs American per name; accent control is mostly via **description text**, not a dedicated `lang_code=b` bank. Third-party fine-tunes (e.g. ParlerVoice) claim British names — **out of scope** unless separately evaluated.

### IELTS fit

| Need | Desk |
|------|------|
| Part 1 (2) | Possible with 2 fixed names + stable descriptions |
| Part 3 (3–4) | **Possible on paper** (34 names) if consistency holds across segments |
| en-GB preference | **Weak / unlisted** for official Mini |
| Re-render | Must freeze **exact same description string** per speaker |
| SSML/phoneme/lexicon | Not Azure-style; description-based prosody |

### Label
`shortlist_lab` as **fixed-cast via description templates** — secondary to Kokoro for en-GB clarity; lab consistency critical.

---

## 2. Orpheus TTS (Canopy)

| Field | Desk finding |
|-------|----------------|
| Source | [canopyai/Orpheus-TTS](https://github.com/canopyai/Orpheus-TTS) |
| Backbone | Llama-class **~3B** speech-LLM |
| License | **Apache-2.0** (repo) |
| English prod voices (**fixed names**) | **8**: `tara`, `leah`, `jess`, `leo`, `dan`, `mia`, `zac`, `zoe` |
| Prompt format | `{name}: <text>` (package can prepend) |
| Extra | Emotive tags; zero-shot cloning also discussed on some model cards (secondary path) |
| Multilingual | Separate research family with **different** voice sets per language |

### Inventory classification

- English finetune-prod: **Type F** — 8 named voices, enough count for Part 3 (2–4).  
- **en-GB:** English list is **not** documented as British-only; treat as **generic English cast**, lab for accent.  
- Larger than Kokoro → may address “too few parameters” concern while keeping fixed names.

### IELTS fit

| Need | Desk |
|------|------|
| Part 1–3 multi-speaker | **Strong on count** (8 fixed) |
| en-GB catalog | **Not documented** like Kokoro `bf_*` |
| Colab | 3B needs VRAM planning (A100 comfortable; L4 may need quant/care) |
| Segment pipeline | One request per segment with same `{name}:` prefix |

### Label
`shortlist_lab` — **best large-ish fixed-name alternative to Kokoro** found in this pass for multi-cast without voice bank.

---

## 3. MeloTTS (refresh)

| Field | Desk finding |
|-------|----------------|
| Source | [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS) |
| License | **MIT** |
| English “inventory” | **Accent packs**: EN-US, **EN-BR**, EN-AU, EN-India, EN-Default |
| Multi-character cast | **No** — choosing EN-BR is one accent line, not 4 distinct people |
| Size / speed | Lightweight; CPU-capable marketing |

### IELTS fit

- Part 2/4 single speaker EN-BR: **useful niche**.  
- Part 1/3 multi-speaker: **does not solve** fixed multi-cast.  
- Label: **optional mono EN-BR**, not primary casting engine.

---

## 4. Voxtral-4B-TTS-2603 (Mistral)

| Field | Desk finding |
|-------|----------------|
| Source | [mistralai/Voxtral-4B-TTS-2603](https://huggingface.co/mistralai/Voxtral-4B-TTS-2603), [Mistral news](https://mistral.ai/news/voxtral-tts/), [arXiv:2603.25551](https://arxiv.org/html/2603.25551v1) |
| Size | **4B** open weights |
| License | **CC BY-NC 4.0** (model inherits non-commercial from reference voice data) |
| Preset voices | **20** named presets (API/local style `voice: "casual_male"`) |
| English presets (community/MLX list) | `casual_male`, `casual_female`, `cheerful_female`, `neutral_male`, `neutral_female` (**5 EN-tagged**) |
| Other presets | fr/es/de/it/pt/nl/ar/hi male/female variants |
| Adaptation | Zero-shot / short reference also supported (~3s) |
| Product API | Also sold via Mistral API (out of budget path); open weights exist for self-host |

### Inventory classification

- **Type F** for the **20 presets** (string voice ids).  
- **Type Z** available for custom refs.  
- EN multi-cast: **~5 English-named presets** → Part 3 **tight** (3–4 EN) but **possible** if all 5 are clearly distinct in lab.  
- Studio marketing mentions American/British/French dialects — **open preset list above is style tags, not a full en-GB bank like Kokoro’s 8**. Lab must verify British-ness of any preset.

### Education no-fee vs NC

- Owner product is **education, no fees** → NC often aligned better than commercial SaaS, but **CC BY-NC still needs a careful read** (attribution, no commercial derivatives, etc.). Flag, not auto-block for private education lab.

### IELTS fit

| Need | Desk |
|------|------|
| Fixed IDs without voice bank | **Yes** (presets) |
| Part 3 3–4 EN | **Borderline** (~5 EN presets) — lab confusability |
| en-GB depth | **Weaker than Kokoro** on documented GB IDs |
| Model size / quality ceiling | **High** (4B) — addresses “Kokoro too small” worry |
| Colab | A100 preferred; 4B BF16 heavy on L4 without quant |

### Label
`shortlist_lab` — **large fixed-preset candidate**; inventory EN thinner than Kokoro but much larger model.

---

## 5. Comparison (this batch + Kokoro baseline)

| Model | Inventory type | Countable EN cast | en-GB story | Size | Fixed without voice bank? | Part 3 multi-cast |
|-------|----------------|-------------------|-------------|------|---------------------------|-------------------|
| **Kokoro** | Pure Type F IDs | 20 US + **8 GB** | **Best documented** | 82M | Yes | Strong |
| **Orpheus EN ft** | Type F names | **8** named | Unspecified accent | ~3B | Yes | Strong on count |
| **Parler Mini v1.1** | Names-in-description | **34** names | Not GB-tagged | ~0.9B | Yes if templates locked | Possible; consistency lab |
| **Voxtral 4B** | Type F presets + Z | **~5 EN** presets | Weak/docs dialect marketing | **4B** | Yes (presets) | Borderline EN count |
| **MeloTTS** | Accent packs | 1 line per accent | **EN-BR pack** | Small | N/A multi-cast | Weak |
| CosyVoice / Qwen Base / Chatterbox | Type Z | Needs refs | Ref-dependent | Large | **No** | Only with bank |

## 6. Impact on selection strategy

Given **no voice bank** + **fixed IDs preferred** + **Kokoro size concern**:

1. **Still inventory-safest for en-GB multi-cast:** Kokoro.  
2. **New large fixed-name option:** **Orpheus** (8 English names) — best “bigger than Kokoro + fixed cast” in this batch.  
3. **New large preset option:** **Voxtral 4B** (20 presets, ~5 EN) — quality ceiling high; EN cast thinner; NC license note.  
4. **Parler Mini v1.1:** fixed **names** via description templates; good English cast size; en-GB not first-class.  
5. **MeloTTS:** EN-BR mono helper only.  
6. Do **not** drop fixed-ID priority for clone-only models unless voice bank is accepted.

**Final backend:** still `not_selected`.  
**Lab:** still required before choosing among Kokoro vs Orpheus vs Voxtral vs Parler.

## 7. Sources

- [parler-tts-mini-v1.1](https://huggingface.co/parler-tts/parler-tts-mini-v1.1)  
- [huggingface/parler-tts](https://github.com/huggingface/parler-tts)  
- [canopyai/Orpheus-TTS](https://github.com/canopyai/Orpheus-TTS)  
- [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS)  
- [mistralai/Voxtral-4B-TTS-2603](https://huggingface.co/mistralai/Voxtral-4B-TTS-2603)  
- [Mistral Voxtral TTS announcement](https://mistral.ai/news/voxtral-tts/)  
