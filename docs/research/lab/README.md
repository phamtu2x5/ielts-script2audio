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

## Compatibility questions this lab answers

1. Can Kokoro take **`spoken_text`** from our manifest without us rewriting the script?  
2. Does **`voice_profile_id` → backend voice** work for 2 speakers?  
3. Do Stage-2 normalisations (spelling, postcode) **help** intelligibility?  
4. Any crash / empty audio / install blocker on Colab?

## Status

| Item | Status |
|------|--------|
| Lab assets in repo | Ready |
| Audio render in this agent session | `NOT_EXECUTED` (needs Colab/GPU + kokoro install) |
| Final TTS selection | `not_selected` |
