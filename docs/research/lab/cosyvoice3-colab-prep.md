# CosyVoice3 Colab prep (short)

## Answers

| Question | Answer |
|----------|--------|
| Colab env ready? | Yes — use GPU runtime |
| Follow CosyVoice docs? | Yes — clone recursive + requirements + HF weight |
| Kokoro audio as ref? | **Yes for lab** — works as zero-shot prompt wav |

## Kokoro → CosyVoice ref (lab)

1. Render Part 1 with Kokoro (`bf_emma` / `bm_george`).
2. Copy two short wavs as refs, e.g.:
   - `seg_0001__bf_emma.wav` → `voice_bank/cosy_refs/spk_a_ref.wav`
   - `seg_0002__bm_george.wav` → `voice_bank/cosy_refs/spk_b_ref.wav`
3. `prompt_text` must match **what that ref said** (use that line’s `spoken_text` / DISPLAY).
4. Map: `configs/voice_maps/cosyvoice3_from_kokoro_part1.json`

Caveats: synthetic ref = CosyVoice clones **Kokoro timbre**, not a real human; quality may be “double TTS”. Fine for lab; later replace with real consented refs if needed.

## Do not

- Install CosyVoice on laptop
- Put emotion tags into `display_text`
- Silent-edit transcript script

## Notebook

`notebooks/colab_cosyvoice3_manifest_lab.ipynb` — numbered cells, sequential run (no Run-all required for Cosy path; no Orpheus-style Restart unless pip breaks ABI).
