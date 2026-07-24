#!/usr/bin/env python3
"""Build CosyVoice zero-shot reference artifacts from Kokoro lab voices.

CosyVoice (docs / load_wav) expects prompt speech at **16 kHz** mono.
prompt_text must match what was spoken in the ref wav.

This script:
  1) Renders short EN lines with Kokoro fixed IDs (default bf_emma / bm_george)
  2) Writes mono PCM WAV at 16 kHz into voice_bank/cosy_refs/
  3) Writes refs_manifest.json + voice_map_runtime.json for CosyVoice3 lab

Does NOT install CosyVoice. Does NOT mutate IELTS display_text scripts.
Lab-only synthetic refs (double-TTS). Not final casting.

Example (Colab):
  python scripts/lab_build_cosyvoice_refs_from_kokoro.py \\
    --out-dir voice_bank/cosy_refs \\
    --lang-code b
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path
from typing import Any


# Short, clean lines — good for zero-shot prompt (avoid long spelling strings)
DEFAULT_SPEAKERS: list[dict[str, str]] = [
    {
        "speaker_key": "spk_a",
        "voice_profile_id": "vp_spk_a",
        "kokoro_voice": "bf_emma",
        "ref_basename": "spk_a_ref.wav",
        # Exact words Kokoro will speak (and CosyVoice prompt_text body)
        "ref_line": "Good morning, City Library. How can I help you?",
    },
    {
        "speaker_key": "spk_b",
        "voice_profile_id": "vp_spk_b",
        "kokoro_voice": "bm_george",
        "ref_basename": "spk_b_ref.wav",
        "ref_line": "Hello. I'd like to join the library, please.",
    },
]

# CosyVoice3 zero_shot examples often prefix assistant + endofprompt
PROMPT_PREFIX = "You are a helpful assistant.<|endofprompt|>"
COSY_PROMPT_SR = 16000  # CosyVoice load_wav(..., 16000)


def _write_wav_int16_mono(path: Path, samples_f32, sample_rate: int) -> None:
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(samples_f32, dtype=np.float32).reshape(-1)
    arr = np.clip(arr, -1.0, 1.0)
    # small tail so last phone is not clipped
    n_pad = int(sample_rate * 0.15)
    if n_pad > 0:
        arr = np.concatenate([arr, np.zeros(n_pad, dtype=np.float32)])
    pcm = (arr * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def _resample_mono(audio, orig_sr: int, target_sr: int):
    import numpy as np

    x = np.asarray(audio, dtype=np.float32).reshape(-1)
    if orig_sr == target_sr:
        return x
    # Prefer torchaudio if available; else linear numpy
    try:
        import torch
        import torchaudio

        t = torch.from_numpy(x).unsqueeze(0)
        y = torchaudio.functional.resample(t, orig_sr, target_sr)
        return y.squeeze(0).numpy().astype(np.float32)
    except Exception:
        duration = len(x) / float(orig_sr)
        n_out = int(round(duration * target_sr))
        if n_out <= 1:
            return x[:1]
        xp = np.linspace(0.0, 1.0, num=len(x), endpoint=False)
        xq = np.linspace(0.0, 1.0, num=n_out, endpoint=False)
        return np.interp(xq, xp, x).astype(np.float32)


def _kokoro_synthesize(text: str, voice: str, lang_code: str) -> tuple[Any, int]:
    """Return (float32 mono audio, sample_rate)."""
    try:
        from kokoro import KPipeline
    except ImportError as exc:
        raise SystemExit(
            "kokoro not installed. On Colab: pip install kokoro soundfile && "
            "apt-get install -y espeak-ng\n"
            f"Original: {exc}"
        ) from exc

    import numpy as np

    pipeline = KPipeline(lang_code=lang_code)
    chunks: list[Any] = []
    sample_rate = 24000
    for result in pipeline(text, voice=voice):
        audio = None
        if hasattr(result, "audio"):
            audio = result.audio
            if getattr(result, "sample_rate", None):
                sample_rate = int(result.sample_rate)
        elif isinstance(result, (tuple, list)):
            for part in result:
                if hasattr(part, "numpy") or (
                    hasattr(part, "shape") and not isinstance(part, str)
                ):
                    audio = part
            if audio is None and len(result) >= 3:
                audio = result[2]
        else:
            audio = result
        if audio is None:
            continue
        if hasattr(audio, "detach"):
            audio = audio.detach().cpu().numpy()
        elif hasattr(audio, "numpy"):
            audio = audio.numpy()
        chunks.append(np.asarray(audio, dtype=np.float32).reshape(-1))
    if not chunks:
        raise RuntimeError(f"Kokoro returned no audio for voice={voice}")
    return np.concatenate(chunks), sample_rate


def build_refs(
    out_dir: Path,
    *,
    lang_code: str = "b",
    speakers: list[dict[str, str]] | None = None,
    prompt_prefix: str = PROMPT_PREFIX,
    target_sr: int = COSY_PROMPT_SR,
) -> dict[str, Any]:
    import numpy as np

    speakers = speakers or DEFAULT_SPEAKERS
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    mapping: dict[str, Any] = {}

    for sp in speakers:
        text = sp["ref_line"].strip()
        voice = sp["kokoro_voice"]
        print(f"Kokoro render {sp['speaker_key']} voice={voice} ...", file=sys.stderr)
        audio, sr = _kokoro_synthesize(text, voice, lang_code)
        audio_16k = _resample_mono(audio, sr, target_sr)
        # peak normalize lightly (avoid clipping)
        peak = float(np.max(np.abs(audio_16k))) if len(audio_16k) else 0.0
        if peak > 1e-6:
            audio_16k = audio_16k * (0.95 / peak)

        wav_path = out_dir / sp["ref_basename"]
        _write_wav_int16_mono(wav_path, audio_16k, target_sr)

        # CosyVoice3-style prompt_text (assistant prefix + body = exact spoken line)
        prompt_text = f"{prompt_prefix}{text}"
        duration_sec = round(len(audio_16k) / float(target_sr), 3)

        # Validate readable wav header
        with wave.open(str(wav_path), "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == target_sr

        entry = {
            "speaker_key": sp["speaker_key"],
            "voice_profile_id": sp["voice_profile_id"],
            "kokoro_voice": voice,
            "lang_code": lang_code,
            "ref_wav": str(wav_path.resolve()),
            "ref_wav_relative": str(Path("voice_bank/cosy_refs") / sp["ref_basename"]),
            "sample_rate_hz": target_sr,
            "channels": 1,
            "sampwidth_bytes": 2,
            "duration_sec": duration_sec,
            "ref_line": text,
            "prompt_text": prompt_text,
            "format_notes": [
                "mono PCM16 WAV",
                f"sample_rate={target_sr} (CosyVoice load_wav target)",
                "prompt_text body equals ref_line spoken by Kokoro",
                "synthetic Kokoro ref — lab only",
            ],
        }
        entries.append(entry)
        mapping[sp["voice_profile_id"]] = {
            "label": f"{sp['speaker_key']}_from_kokoro_{voice}",
            "ref_wav": str(wav_path.resolve()),
            "ref_wav_relative": entry["ref_wav_relative"],
            "prompt_text": prompt_text,
            "ref_line": text,
            "kokoro_voice": voice,
            "sample_rate_hz": target_sr,
            "default_instruct": (
                "You are a helpful assistant. Speak clearly and calmly in English."
                "<|endofprompt|>"
            ),
        }
        print(
            json.dumps(
                {
                    "speaker": sp["speaker_key"],
                    "wav": str(wav_path),
                    "sr": target_sr,
                    "duration_sec": duration_sec,
                },
                ensure_ascii=False,
            )
        )

    manifest = {
        "artifact_type": "cosyvoice_zero_shot_refs",
        "generator": "kokoro",
        "target_format": {
            "sample_rate_hz": target_sr,
            "channels": 1,
            "pcm": "int16",
            "prompt_text_rule": "PROMPT_PREFIX + exact spoken ref_line",
            "prompt_prefix": prompt_prefix,
            "cosyvoice_api": "inference_zero_shot(tts_text, prompt_text, prompt_wav)",
            "docs": "https://github.com/FunAudioLLM/CosyVoice",
        },
        "speakers": entries,
        "lab_only": True,
        "not_final_tts_selection": True,
    }

    man_path = out_dir / "refs_manifest.json"
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    voice_map = {
        "backend": "fun-cosyvoice3-0.5b-2512",
        "mode_default": "zero_shot",
        "ref_source": "kokoro_synthetic",
        "mapping": mapping,
        "tense_instruct": (
            "You are a helpful assistant. Speak slightly faster, more urgent and tense."
            "<|endofprompt|>"
        ),
        "model_dir": "pretrained_models/Fun-CosyVoice3-0.5B",
        "hf_model_id": "FunAudioLLM/Fun-CosyVoice3-0.5B-2512",
        "refs_manifest": str(man_path.resolve()),
    }
    map_path = out_dir / "voice_map_runtime.json"
    map_path.write_text(json.dumps(voice_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {man_path}", file=sys.stderr)
    print(f"Wrote {map_path}", file=sys.stderr)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build CosyVoice 16k ref wavs + prompt_text from Kokoro"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("voice_bank/cosy_refs"),
        help="Output directory for ref wavs and manifests",
    )
    parser.add_argument(
        "--lang-code",
        default="b",
        help="Kokoro lang_code (b=British English)",
    )
    parser.add_argument(
        "--target-sr",
        type=int,
        default=COSY_PROMPT_SR,
        help="CosyVoice prompt sample rate (default 16000)",
    )
    args = parser.parse_args(argv)
    build_refs(args.out_dir, lang_code=args.lang_code, target_sr=args.target_sr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
