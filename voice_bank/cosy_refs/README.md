# CosyVoice reference wavs (lab)

## Required format (CosyVoice zero-shot)

| Field | Value |
|-------|--------|
| Audio | mono, 16-bit PCM WAV |
| Sample rate | **16000 Hz** (`load_wav(..., 16000)` in CosyVoice docs) |
| prompt_text | Must match words spoken in the wav |
| Prefix (CV3) | Often `You are a helpful assistant.<\|endofprompt|>` + body |

## How to generate (recommended)

Colab notebook: `notebooks/colab_build_cosyvoice_refs_from_kokoro.ipynb`

```bash
python scripts/lab_build_cosyvoice_refs_from_kokoro.py --out-dir voice_bank/cosy_refs
```

Produces:

- `spk_a_ref.wav` — Kokoro `bf_emma`
- `spk_b_ref.wav` — Kokoro `bm_george`
- `refs_manifest.json`
- `voice_map_runtime.json`

Synthetic Kokoro refs are **lab-only**. Replace with real consented speech later if needed.

Wav files are gitignored (`*.wav` / `voice_bank/*.wav`).
