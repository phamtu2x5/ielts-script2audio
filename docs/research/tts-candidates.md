# TTS candidates (desk research)

**Date:** 2026-07-20 (rev.2 — constraints Colab + open-weight)  
**Method:** Web/docs desk research — benchmark audio **`NOT_EXECUTED`**.  
**Rule:** Không chọn final backend từ desk alone.  
**Không** silent-edit script; vấn đề transcript → báo owner.

Licensing phải verify lại trước pilot. Giá API chỉ mang tính tham chiếu.

---

## Constraints ảnh hưởng research (xem thêm `deployment-constraints.md`)

| Constraint | Ảnh hưởng shortlist |
|------------|---------------------|
| Runtime = **Colab L4/A100**, repo + notebook | Ưu tiên open-weight CUDA; notebook-friendly |
| **Không** lấy laptop local làm host model chính | Bỏ prior “phải siêu nhẹ chỉ để CPU laptop” |
| GPU mạnh → **được** xét model **~0.3B–1B+** | Không chỉ Kokoro ~80M |
| API thương mại = **research-only** (thiếu budget) | Azure/Polly/Google/ElevenLabs **không** prior triển khai |
| SSML/phoneme/lexicon | Quan trọng dài hạn; **không** quyết prior chọn TTS lúc này |
| Phải kiểm **số giọng + accent** vs IELTS Part (nhất là Part 3) | Cloning / fixed voices / zero-shot ref wav |

---

## A. Open-weight (prior triển khai + lab)

### A1. CosyVoice 2 / Fun-CosyVoice 3 (0.3B–0.5B) — **shortlist lab ưu tiên**

| Field | Desk finding |
|-------|----------------|
| **Nguồn** | [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice) |
| **Scale** | CosyVoice-**300M**; CosyVoice2-**0.5B**; Fun-CosyVoice3-**0.5B** (+ RL variant) — **phù hợp L4/A100**, không bị kẹt “model nhỏ only” |
| **Multi-speaker** | (1) **Zero-shot cloning** từ clip tham chiếu; (2) biến thể **SFT / Instruct** với speaker/style control. Dialogue nhiều nhân vật: **một ref/voice profile mỗi speaker**, render theo turn — không phải “tự động 4 mic” |
| **English / accent** | English nằm trong multi-lingual (9 ngôn ngữ). **British English không được docs nhấn riêng** — chỉ “English” chung + nhiều dialect **Chinese**. → **Rủi ro en-GB**: phải lab với ref wav GB hoặc SFT voice; không assume có catalog “en-GB-Neural2” kiểu Azure |
| **Pronunciation** | Có hướng phoneme (English **CMU** phonemes / inpainting — desk). Không thay SSML Azure; vẫn dựa `spoken_text` |
| **License (desk)** | **Apache-2.0** (repo) — rõ hơn XTTS weights history |
| **Colab** | Stack NVIDIA (Docker/CUDA, optional TensorRT/vLLM). Cần notebook cài deps + download weights trên runtime Colab |
| **Risks** | Inventory “fixed voices” vs bắt buộc thu thập **ref audio** có consent; en-GB quality; long-form Part 4; effort notebook |
| **Desk label** | `shortlist_lab` (**priority 1** dưới constraint mới) |

### A2. F5-TTS — **shortlist lab có điều kiện license**

| Field | Desk finding |
|-------|----------------|
| **Nguồn** | [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS) |
| **Scale** | DiT-based; “Base” naming; **không** quảng cáo “vài chục M” — nặng hơn Kokoro; chạy GPU (có report RTF trên L20). Phù hợp Colab class |
| **Multi-speaker** | **Zero-shot / multi-style**: `ref_audio` + `ref_text` (kể cả multi-voice story config). **Không** fixed bank 20 voice có sẵn kiểu Polly |
| **English** | Train Emilia **ZH–EN** → English OK |
| **License (desk)** | Code **MIT**; pretrained weights **CC-BY-NC** (vì data Emilia) → **`[OPEN-QUESTION]` commercial**: nếu project cần commercial release, **weights NC có thể chặn** |
| **Colab** | GPU NVIDIA supported; empty `ref_text` kích ASR tốn VRAM thêm |
| **Risks** | **NC weights**; cần ref wav per speaker; accent GB phụ thuộc ref |
| **Desk label** | `shortlist_lab` **chỉ non-commercial / research lab** cho đến khi license OK; **hold commercial pilot** |

### A3. Kokoro (~82M) — **baseline lab (vẫn giữ)**

| Field | Desk finding |
|-------|----------------|
| **Nguồn** | [hexgrad/kokoro](https://github.com/hexgrad/kokoro) |
| **Scale** | ~**82M** — nhẹ; vẫn hữu ích trên Colab (nhanh, rẻ VRAM) dù **không** còn là ceiling |
| **Multi-speaker** | Voice **ids / packs** có sẵn (vd. `af_heart`) + lang codes (gồm British/American English) — **dễ map `voice_profile_id`** hơn pure cloning |
| **Accent** | Có **British English** trong lang/voice story desk — **điểm cộng** so với “English chung” |
| **License** | Apache-2.0 claim |
| **Vai trò** | Baseline tốc độ + inventory voice id; so với model 0.5B |
| **Desk label** | `shortlist_lab` (**baseline**, không phải “model chính chỉ vì nhỏ”) |

### A4. Piper / ONNX multi-voice files — **optional baseline**

- Nhiều voice file, rất nhanh, naturalness desk expectation thấp hơn.  
- License **từng voice**.  
- Label: optional control; **không** ưu tiên nếu đã có Kokoro + CosyVoice.

### A5. Coqui XTTS-v2 — **hold**

| Field | Desk finding |
|-------|----------------|
| **Nguồn** | [coqui-ai/TTS](https://github.com/coqui-ai/TTS) |
| **Multi-speaker** | Mạnh (cloning `speaker_wav`) |
| **License** | Code MPL-2.0; **weights historically CPML/non-commercial risk** → verify trước lab |
| **Maintenance** | Toolkit release ~2023; momentum risk |
| **Desk label** | `research_only` until license weights + consent policy clear |

### A6. Dia / “dialogue-native” TTS (Nari-class) — **research_only theo dõi**

- Hướng model **sinh dialogue multi-speaker** trong một hệ (khác render từng turn).  
- Desk: thú vị cho Part 1/3 nhưng maturity, license, accent control, segment re-render theo manifest **chưa** đủ để shortlist vòng 1.  
- Theo dõi khi lab open-weight ổn định.

### A7. StyleTTS2 / pure research checkpoints — **research_only**

Naturalness paper cao; productization + multi-speaker inventory + Colab notebook effort lớn.

---

## B. Managed API — **research-only** (không prior triển khai)

Giữ để **học** SSML/phoneme/lexicon và đối chiếu chất lượng sau này khi có budget.  
**Không** đưa vào “phải có account để làm Stage 4”.

| Candidate | Research value | Triển khai hiện tại |
|-----------|----------------|---------------------|
| **Azure Neural TTS** | SSML, phoneme, lexicon, catalog en-GB | Out-of-budget → docs only |
| **Amazon Polly** | SSML + lexicons, billing AWS | Research-only |
| **Google Cloud TTS** | Neural2, SSML | Research-only |
| **ElevenLabs-class** | Naturalness | Research-only; codes TBD |

Chi tiết API cũ vẫn đúng về mặt tính năng; **prior đã hạ** theo OQ-07.

---

## C. Hybrid

Với budget API thấp: hybrid “local Colab + Azure answer spans” **không khả thi** như path chính.  
Hybrid thực tế hiện tại: **Colab open-weight only**; sau này API optional.

---

## D. So sánh desk (open-weight focus)

| Candidate | ~Scale | Voices / multi-spk | Accent EN/GB (desk) | License clarity | Colab L4/A100 | Lab priority |
|-----------|--------|--------------------|---------------------|-----------------|---------------|--------------|
| **CosyVoice 2/3** | 0.3–0.5B | Zero-shot + SFT/Instruct | EN yes; **GB unspecified** | Apache (desk) | Yes | **1** |
| **F5-TTS** | Base DiT (GPU) | Zero-shot ref | EN (Emilia) | Code MIT; **weights NC** | Yes | **2** (non-commercial first) |
| **Kokoro** | ~82M | Fixed voice ids | **EN-GB path desk** | Apache claim | Yes (light) | **Baseline** |
| Piper | Small ONNX | Many files | Per voice | Per voice | Yes | Optional |
| XTTS | Large cloning | Zero-shot | Ref-dependent | **Weights risk** | Yes | Hold |
| Azure etc. | API | Huge catalog | Strong GB catalog | Commercial ToS | N/A | Research-only |

---

## E. Ràng buộc giọng / accent cho IELTS (checklist research)

Khi **chọn hoặc lab** model open-weight, phải trả lời được:

1. **Part 1:** ≥2 giọng content phân biệt (nam/nữ hoặc timbre khác).  
2. **Part 2 & 4:** 1 giọng monologue ổn định dài.  
3. **Part 3:** **2–4** giọng content — nghe phân biệt **không** cần transcript.  
4. Narrator (sau này): khác content (delivery full_exam).  
5. **Accent:** ưu tiên English rõ; **en-GB** nếu có (Kokoro desk có hướng GB; CosyVoice/F5 phụ thuộc ref/SFT).  
6. **Nguồn giọng:** fixed id vs **ref wav** — nếu ref wav: **consent** + không stereotype.  
7. **Re-render:** cùng speaker + cùng ref/id → giọng không “đổi người”.

Nếu model chỉ zero-shot mà **không** có bộ ref wav có kiểm soát → project phải **tự xây voice bank** (thêm việc, không free).

---

## F. Evidence still required

1. Lab trên Colab: CosyVoice và/hoặc F5-TTS + Kokoro baseline, Part 1–3.  
2. Đếm **inventory** thực tế (ids hoặc ref set) ≥ Part 3.  
3. Nghe **en-GB** hoặc English đủ “IELTS-like”.  
4. Codes: spelling, postcode, phone với `spoken_text` Stage 2.  
5. License snapshot (đặc biệt F5-TTS NC, XTTS weights).  
6. Notebook template + git pull workflow documented.  

---

## Sources

- [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice)  
- [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)  
- [hexgrad/kokoro](https://github.com/hexgrad/kokoro)  
- [coqui-ai/TTS](https://github.com/coqui-ai/TTS)  
- Azure TTS/SSML docs (research-only reference)  
- `docs/prompts/system-control.md` §19  
