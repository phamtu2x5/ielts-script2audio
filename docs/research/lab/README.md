# Lab: inference against Stage 1–2 manifests

## Purpose

Test whether a TTS model can **use the prepared pipeline output**:

```text
transcript JSON
  → ielts-s2a prepare
  → synthesis manifest (requests[].spoken_text, voice_profile_id, …)
  → voice map
  → lab renderer
  → wav + report
```

Not production Stage 4. Not final model selection.

## Recommended first lab: Kokoro + Part 1

### Why Kokoro first
- Fixed voice IDs (no voice bank)
- en-GB voices available
- Light on Colab
- Clear map from `vp_spk_a` / `vp_spk_b`

### Multi-voice survey (same lines, many Kokoro IDs)

After `prepare` has produced `outputs/part1_manifest.json`:

```bash
python scripts/lab_survey_kokoro_voices.py \
  --manifest outputs/part1_manifest.json \
  --inventory configs/voice_maps/kokoro_voice_inventory.json \
  --preset gb_core \
  --out-dir lab_audio/kokoro_voice_survey \
  --event-ids e004,e006,e008,e011
```

| Preset | Voices |
|--------|--------|
| `gb_core` | All 8 British (`bf_*` / `bm_*`) |
| `gb_shortlist` | emma, george, fable, isabella |
| `us_sample` | Optional 4 US voices |

Notebook section **§8** walks through listening **by event_id** (same SPOKEN, different voices).

### Files
| File | Role |
|------|------|
| `examples/part1_valid.json` | Stage-1 input |
| `outputs/part1_manifest.json` | Generate locally/Colab via prepare (gitignored under outputs/) |
| `configs/voice_maps/kokoro_en_gb_part1.json` | voice_profile_id → Kokoro id |
| `scripts/lab_render_kokoro_from_manifest.py` | Lab renderer |
| `notebooks/colab_kokoro_manifest_lab.ipynb` | Colab walkthrough |
| `checklist-stage1-2-compatibility.md` | What to verify |

## Colab steps (summary)

1. Runtime → GPU (L4/A100 if available).  
2. Clone repo: `https://github.com/phamtu2x5/ielts-script2audio.git` (notebook already uses this URL).  
3. Install:
   ```bash
   pip install -e ".[dev]" kokoro soundfile
   apt-get update && apt-get install -y espeak-ng
   ```
4. Prepare manifest:
   ```bash
   ielts-s2a prepare examples/part1_valid.json -o outputs/part1_manifest.json
   ```
5. Render:
   ```bash
   python scripts/lab_render_kokoro_from_manifest.py \
     --manifest outputs/part1_manifest.json \
     --voice-map configs/voice_maps/kokoro_en_gb_part1.json \
     --out-dir lab_audio/kokoro_part1
   ```
6. Listen + fill checklist.  
7. Write short notes in `notes-kokoro-part1.md` (create when done).

## Tracking từng câu (một cách duy nhất trong notebook)

Notebook **chỉ** dùng một phương pháp:

1. Cell **§5**: lần lượt từng segment — in `DISPLAY` + `SPOKEN` + `Audio()`.  
2. Cell **§5b**: điền dict `reviews` (`yes` / `partial` / `no` + notes) → lưu `segment_review_filled.json`.

Không dùng HTML table / CSV / terminal **trong notebook** (tránh nhiễu).  
CSV/`lab_show_segment_tracking.py` vẫn có thể có từ script render (phụ, ngoài notebook) nếu cần export sau.

### Cách đối chiếu

Với mỗi segment:

1. Đọc `DISPLAY` (script gốc — không sửa).  
2. Đọc `SPOKEN` (text Stage-2 đưa TTS).  
3. Nghe audio ngay dưới.  
4. Ghi `yes` / `partial` / `no` trong `reviews`.  

### Files chính sau lab

```text
lab_audio/kokoro_part1/
  seg_*.wav
  lab_render_report.json
  segment_review_filled.json   # sau §5b
```

## Compatibility questions this lab answers

1. Can Kokoro take **`spoken_text`** from our manifest without us rewriting the script?  
2. Does **`voice_profile_id` → backend voice** work for 2 speakers?  
3. Do Stage-2 normalisations (spelling, postcode) **help** intelligibility?  
4. Any crash / empty audio / install blocker on Colab?  
5. Per segment: does audio **content** match display/spoken expectations?

## Orpheus lab (second backend)

Notebook: `notebooks/colab_orpheus_manifest_lab.ipynb`

| Item | Path |
|------|------|
| Part 1 voice map | `configs/voice_maps/orpheus_en_part1.json` (tara / leo) |
| Inventory + presets | `configs/voice_maps/orpheus_voice_inventory.json` |
| Dialogue render | `scripts/lab_render_orpheus_from_manifest.py` |
| Multi-voice survey | `scripts/lab_survey_orpheus_voices.py` |

Install (local open-weight, **not** paid API):

```bash
pip install orpheus-speech
# if vLLM breaks: pip install vllm==0.7.3
```

Model: `canopylabs/orpheus-tts-0.1-finetune-prod`  
Voices: `tara, leah, jess, leo, dan, mia, zac, zoe` (no official en-GB bank).

Uses the **same** `ielts-s2a prepare` manifest as Kokoro for fair comparison.

## Status

| Item | Status |
|------|--------|
| Kokoro lab assets | Ready |
| Orpheus lab assets | Ready (notebook + scripts) |
| Audio render in agent session | `NOT_EXECUTED` (needs your Colab/GPU) |
| Final TTS selection | `not_selected` |
