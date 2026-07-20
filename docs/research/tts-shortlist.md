# TTS shortlist & recommendation status

**Date:** 2026-07-20 (rev.2)  
**Mode:** C — research  
**Final backend:** **`not_selected`**

## 1. Recommendation status

```text
status: shortlist_pending_lab
final_selection: none
benchmark_execution: NOT_EXECUTED
deployment: colab_open_weight   # OQ-06 user-provided
api_commercial: research_only   # OQ-07 budget
```

## 2. Prior đã đổi (quan trọng)

| Trước (desk v1) | Sau (constraints user) |
|-----------------|------------------------|
| Azure gần đầu shortlist vì SSML | API = **research-only** (thiếu budget) |
| Ưu tiên model nhỏ / local laptop | **Colab L4/A100**; model **0.3B–0.5B+** được khuyến khích cân nhắc |
| SSML là lý do chọn vendor | SSML/phoneme/lexicon **vẫn cần** dài hạn nhưng **không** quyết prior hiện tại |

## 3. Shortlist lab (open-weight / Colab)

| Priority | Candidate | ~Scale | Voices / accent (desk) | Blockers before pilot |
|----------|-----------|--------|------------------------|------------------------|
| **Inventory-safe first** | **Kokoro** | ~82M | **Type F:** 20 EN-US + **8 EN-GB** fixed IDs | Lab quality GB + Part 3 confusability |
| **Type F limited EN** | **Qwen3-TTS CustomVoice** | 0.6B/1.7B | **9** named; only **~2 English** (Ryan, Aiden, US-leaning) | Part 3 3–4 EN gap |
| **Not Base for fixed IDs** | **Qwen3-TTS 1.7B Base** | 1.7B | **Type Z clone only** | Needs refs — same as no voice bank problem |
| **Scale/quality next** | **CosyVoice 2/3** | 0.3–0.5B | **Type Z** | Voice bank required |
| **Alt Type Z** | **F5-TTS**, **Chatterbox Multilingual** | DiT / ~500M | Type Z | Voice bank required |
| **Product/API-ish** | **Fish S2 Pro** | — | Not verified open fixed bank for Colab | research_only |
| **Mono EN-BR only** | **MeloTTS** | small | Accent packs EN-BR etc., not multi-cast | Part 2/4 niche only |
| **Large fixed names** | **Orpheus EN ft** | ~3B | **8** English names (tara, leah, jess, leo, dan, mia, zac, zoe) | Accent not GB-tagged; VRAM |
| **Description-cast** | **Parler Mini v1.1** | ~0.9B | **34** speaker names in description text | Lock templates; en-GB weak |
| **Large presets** | **Voxtral-4B-TTS-2603** | **4B** | **20** presets; **~5 EN** ids | EN cast tight for Part 3; CC-BY-NC; VRAM |
| Optional | Piper | Small | Many files | Chỉ control tốc độ |
| Hold | Coqui XTTS | Cloning | Ref | License weights + maintenance |
| Research-only | Azure / Polly / Google / ElevenLabs | API | Catalog mạnh / SSML | **Budget** — không triển khai chính |

## 4. Provisional lean (sau lab, có thể đổi)

```text
Primary path:   open-weight on Colab (CosyVoice-class or winner of lab)
Baseline:       Kokoro for fast iteration / voice-id mapping
API:            research reference only until budget
Manifest:       always TTS-neutral (ADR-0002)
Voice strategy: fixed ids if available; else controlled ref-wav bank + consent
```

## 5. Voice / accent gate (bắt buộc khi lab)

Không shortlist “xong” nếu chưa trả lời:

- [ ] ≥2 giọng Part 1 phân biệt  
- [ ] 1 giọng ổn định Part 2/4  
- [ ] 3–4 giọng Part 3 nghe ra speaker không cần transcript  
- [ ] Accent: English rõ; en-GB nếu có (ref hoặc voice id)  
- [ ] Re-render cùng voice_profile không lạc giọng  
- [ ] Nguồn giọng: id có sẵn **hoặc** ref wav + consent  

## 6. Evidence still required

- [ ] Colab notebook: setup + `git pull` + prepare manifest + render  
- [ ] Lab scores trên B-P1…B-P3 (tối thiểu)  
- [ ] Codes với `spoken_text` (spelling, postcode, phone)  
- [ ] License snapshot (CosyVoice Apache; F5-TTS NC)  
- [ ] Quyết định commercial vs research-only cho F5-TTS  
- [ ] Chính sách ref wav / voice bank  

## 7. Next experiment (nhỏ nhất, khớp Colab)

1. Push repo git (nếu chưa).  
2. Notebook Colab: clone repo, `pip install -e ".[dev]"`, `prepare` Part 1.  
3. Smoke **một** open-weight: **Kokoro** (nhẹ, voice id) **hoặc** CosyVoice (nếu sẵn sàng VRAM/time).  
4. Ghi listening notes vào `docs/research/lab/` (postcode, spelling, 2 speakers).  
5. **Không** production adapter; **không** chọn final; **không** sửa script im lặng.

## 8. Không được phép từ Stage 3

- Claim đã chọn TTS production.  
- Hard-code vendor vào domain core.  
- Tự sửa transcript/script.  
- Coi API research docs là đã deploy được khi không có budget.  
