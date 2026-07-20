#!/usr/bin/env python3
"""Lab-only: render Kokoro audio from a Stage-2 synthesis manifest.

Purpose
-------
Check compatibility with Stage 1–2 outputs (manifest requests, spoken_text,
voice_profile_id mapping). This is NOT production Stage-4 adapter packaging.

Does not:
- mutate display_text / transcript script
- claim final TTS selection
- run unless dependencies (kokoro, soundfile, torch) are installed

Typical Colab usage:
  !git clone <repo> && cd <repo>
  !pip install -e ".[dev]" kokoro soundfile
  !apt-get install -y espeak-ng
  !python scripts/lab_render_kokoro_from_manifest.py \\
      --manifest outputs/part1_manifest.json \\
      --voice-map configs/voice_maps/kokoro_en_gb_part1.json \\
      --out-dir lab_audio/kokoro_part1
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_voice(
    voice_profile_id: str,
    voice_map: dict[str, Any],
) -> tuple[str, str]:
    mapping = voice_map.get("mapping") or {}
    entry = mapping.get(voice_profile_id)
    if entry and entry.get("backend_voice_id"):
        return entry["backend_voice_id"], voice_map.get("lang_code", "b")
    fallback = voice_map.get("fallback_voice", "bf_emma")
    return fallback, voice_map.get("lang_code", "b")


def _write_wav_pcm16(path: Path, audio, sample_rate: int) -> None:
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(audio, dtype=np.float32)
    # clip and convert to int16
    arr = np.clip(arr, -1.0, 1.0)
    pcm = (arr * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def render_manifest(
    manifest_path: Path,
    voice_map_path: Path,
    out_dir: Path,
    *,
    use_spoken_text: bool = True,
    limit: int | None = None,
) -> dict[str, Any]:
    try:
        from kokoro import KPipeline
    except ImportError as exc:
        raise SystemExit(
            "kokoro is not installed. On Colab: pip install kokoro soundfile && "
            "apt-get install -y espeak-ng\n"
            f"Original error: {exc}"
        ) from exc

    import numpy as np

    manifest = _load_json(manifest_path)
    voice_map = _load_json(voice_map_path)
    requests = list(manifest.get("requests") or [])
    if limit is not None:
        requests = requests[:limit]

    # One pipeline per lang_code used
    pipelines: dict[str, Any] = {}
    report: dict[str, Any] = {
        "manifest_id": manifest.get("manifest_id"),
        "transcript_id": manifest.get("transcript_id"),
        "backend": "kokoro",
        "text_field_used": "spoken_text" if use_spoken_text else "display_text",
        "segments": [],
        "ok_count": 0,
        "fail_count": 0,
        "compatibility_notes": [],
    }

    # Quick schema compatibility checks (Stage 1–2 contract)
    required = {
        "request_id",
        "segment_id",
        "speaker_id",
        "voice_profile_id",
        "spoken_text",
        "display_text",
    }
    if requests:
        missing = required - set(requests[0].keys())
        if missing:
            report["compatibility_notes"].append(
                f"manifest request missing keys: {sorted(missing)}"
            )
        else:
            report["compatibility_notes"].append(
                "manifest request keys include Stage-2 TTS-neutral fields"
            )

    out_dir.mkdir(parents=True, exist_ok=True)

    for req in requests:
        seg_id = req.get("segment_id", "unknown")
        vp = req.get("voice_profile_id") or ""
        text = (
            req.get("spoken_text") if use_spoken_text else req.get("display_text")
        ) or ""
        voice_id, lang_code = _resolve_voice(vp, voice_map)

        item: dict[str, Any] = {
            "segment_id": seg_id,
            "request_id": req.get("request_id"),
            "speaker_id": req.get("speaker_id"),
            "voice_profile_id": vp,
            "backend_voice_id": voice_id,
            "lang_code": lang_code,
            "text_preview": text[:80],
            "status": "PENDING",
            "output": None,
            "error": None,
        }

        try:
            if lang_code not in pipelines:
                pipelines[lang_code] = KPipeline(lang_code=lang_code)
            pipeline = pipelines[lang_code]

            chunks: list[Any] = []
            sample_rate = 24000
            for result in pipeline(text, voice=voice_id):
                # kokoro yields objects/tuples depending on version — handle common shapes
                audio = None
                if hasattr(result, "audio"):
                    audio = result.audio
                    if getattr(result, "sample_rate", None):
                        sample_rate = int(result.sample_rate)
                elif isinstance(result, (tuple, list)) and len(result) >= 2:
                    # (graphemes, phonemes, audio) or similar
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
                raise RuntimeError("Kokoro returned no audio chunks")

            audio_out = np.concatenate(chunks)
            out_path = out_dir / f"{seg_id}__{voice_id}.wav"
            _write_wav_pcm16(out_path, audio_out, sample_rate)
            item["status"] = "EXECUTED"
            item["output"] = str(out_path)
            item["num_samples"] = int(audio_out.shape[0])
            item["sample_rate"] = sample_rate
            report["ok_count"] += 1
        except Exception as exc:  # lab must record failures honestly
            item["status"] = "FAILED"
            item["error"] = f"{type(exc).__name__}: {exc}"
            report["fail_count"] += 1

        report["segments"].append(item)
        print(json.dumps(item, ensure_ascii=False))

    report_path = out_dir / "lab_render_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {report_path}", file=sys.stderr)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lab render: Kokoro ← Stage-2 synthesis manifest"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to synthesis manifest JSON from ielts-s2a prepare",
    )
    parser.add_argument(
        "--voice-map",
        type=Path,
        required=True,
        help="Path to voice map JSON (voice_profile_id → backend_voice_id)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("lab_audio/kokoro"),
        help="Directory for wav + lab_render_report.json",
    )
    parser.add_argument(
        "--use-display-text",
        action="store_true",
        help="Ablation: feed display_text instead of spoken_text",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only first N requests (smoke)",
    )
    args = parser.parse_args(argv)

    report = render_manifest(
        args.manifest,
        args.voice_map,
        args.out_dir,
        use_spoken_text=not args.use_display_text,
        limit=args.limit,
    )
    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
