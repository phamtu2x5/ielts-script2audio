#!/usr/bin/env python3
"""Lab-only: render Orpheus audio from a Stage-2 synthesis manifest.

Uses local open-weight Orpheus via `orpheus-speech` / OrpheusModel + vLLM
(see https://github.com/canopyai/Orpheus-TTS).

Does NOT use the paid OrpheusClient API (`pip install orpheus-tts`).

Does not:
- mutate display_text / transcript script
- claim final TTS selection

Example:
  python scripts/lab_render_orpheus_from_manifest.py \\
    --manifest outputs/part1_manifest.json \\
    --voice-map configs/voice_maps/orpheus_en_part1.json \\
    --out-dir lab_audio/orpheus_part1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import wave
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_voice(voice_profile_id: str, voice_map: dict[str, Any]) -> str:
    mapping = voice_map.get("mapping") or {}
    entry = mapping.get(voice_profile_id) or {}
    if entry.get("backend_voice_id"):
        return str(entry["backend_voice_id"])
    return str(voice_map.get("fallback_voice") or "tara")


def _write_wav_pcm16_bytes(
    path: Path,
    pcm_bytes: bytes,
    sample_rate: int = 24000,
    *,
    end_pad_ms: int = 0,
) -> int:
    """Write mono int16 PCM; return total frame count including pad."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pad_ms = max(0, int(end_pad_ms))
    n_pad = int(sample_rate * pad_ms / 1000) if pad_ms else 0
    pad = b"\x00\x00" * n_pad
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes + pad)
    return (len(pcm_bytes) // 2) + n_pad


def _end_pad_ms_for_request(req: dict[str, Any], default_ms: int, codes_ms: int) -> int:
    protected = req.get("protected_region_ids") or []
    spoken = req.get("spoken_text") or ""
    if protected or "..." in spoken:
        return max(default_ms, codes_ms)
    return default_ms


def _generate_pcm(
    model: Any,
    text: str,
    voice: str,
    *,
    temperature: float,
    repetition_penalty: float,
    max_tokens: int,
) -> bytes:
    chunks: list[bytes] = []
    # OrpheusModel.generate_speech yields audio byte chunks (int16 PCM)
    stream = model.generate_speech(
        prompt=text,
        voice=voice,
        temperature=temperature,
        repetition_penalty=repetition_penalty,
        max_tokens=max_tokens,
    )
    for audio_chunk in stream:
        if audio_chunk is None:
            continue
        if isinstance(audio_chunk, (bytes, bytearray)):
            chunks.append(bytes(audio_chunk))
        elif hasattr(audio_chunk, "tobytes"):
            chunks.append(audio_chunk.tobytes())
        else:
            chunks.append(bytes(audio_chunk))
    if not chunks:
        raise RuntimeError("Orpheus returned no audio chunks")
    return b"".join(chunks)


def render_manifest(
    manifest_path: Path,
    voice_map_path: Path,
    out_dir: Path,
    *,
    use_spoken_text: bool = True,
    limit: int | None = None,
    model_name: str | None = None,
    max_model_len: int = 2048,
    temperature: float = 0.6,
    repetition_penalty: float = 1.3,
    max_tokens: int = 1200,
    end_pad_ms: int = 250,
    codes_end_pad_ms: int = 550,
    sample_rate: int = 24000,
) -> dict[str, Any]:
    try:
        from orpheus_tts import OrpheusModel
    except Exception as exc:
        # ImportError OR OSError (e.g. missing libcudart.so.13 from wrong vLLM wheel)
        raise SystemExit(
            "orpheus_tts / OrpheusModel not available.\n"
            "Common Colab cause: vLLM wheel expects CUDA 13 (libcudart.so.13) but "
            "runtime only has CUDA 12.x.\n\n"
            "Fix on Colab (open-weight, not API):\n"
            "  pip uninstall -y orpheus-tts 2>/dev/null || true\n"
            "  pip install orpheus-speech\n"
            "  pip install vllm==0.7.3\n"
            "  Runtime → Restart session, re-run install\n\n"
            "Official Orpheus Colab: "
            "https://colab.research.google.com/drive/1KhXT56UePPUHhqitJNUxq63k-pQomz3N\n"
            "Upstream: https://github.com/canopyai/Orpheus-TTS\n"
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc

    manifest = _load_json(manifest_path)
    voice_map = _load_json(voice_map_path)
    model_id = (
        model_name
        or voice_map.get("model_name")
        or "canopylabs/orpheus-tts-0.1-finetune-prod"
    )
    requests = list(manifest.get("requests") or [])
    event_by_segment = {
        s.get("segment_id"): s.get("event_id")
        for s in (manifest.get("segments") or [])
        if s.get("segment_id")
    }
    if limit is not None:
        requests = requests[:limit]

    print(f"Loading OrpheusModel {model_id} (max_model_len={max_model_len})...", file=sys.stderr)
    model = OrpheusModel(model_name=model_id, max_model_len=max_model_len)

    report: dict[str, Any] = {
        "manifest_id": manifest.get("manifest_id"),
        "transcript_id": manifest.get("transcript_id"),
        "backend": "orpheus",
        "model_name": model_id,
        "text_field_used": "spoken_text" if use_spoken_text else "display_text",
        "temperature": temperature,
        "repetition_penalty": repetition_penalty,
        "sample_rate": sample_rate,
        "end_pad_ms_default": end_pad_ms,
        "codes_end_pad_ms": codes_end_pad_ms,
        "segments": [],
        "ok_count": 0,
        "fail_count": 0,
        "compatibility_notes": [
            "Uses Stage-2 TTS-neutral requests; maps voice_profile_id → Orpheus fixed name",
            "Does not use paid OrpheusClient API",
        ],
    }

    out_dir.mkdir(parents=True, exist_ok=True)

    for req in requests:
        seg_id = req.get("segment_id", "unknown")
        vp = req.get("voice_profile_id") or ""
        text = (
            req.get("spoken_text") if use_spoken_text else req.get("display_text")
        ) or ""
        voice_id = _resolve_voice(vp, voice_map)

        item: dict[str, Any] = {
            "segment_id": seg_id,
            "request_id": req.get("request_id"),
            "event_id": req.get("event_id") or event_by_segment.get(seg_id),
            "speaker_id": req.get("speaker_id"),
            "voice_profile_id": vp,
            "backend_voice_id": voice_id,
            "display_text": req.get("display_text") or "",
            "spoken_text": req.get("spoken_text") or "",
            "text_fed_to_tts": text,
            "text_field_used": "spoken_text" if use_spoken_text else "display_text",
            "protected_region_ids": list(req.get("protected_region_ids") or []),
            "status": "PENDING",
            "output": None,
            "output_filename": None,
            "error": None,
            "human_content_match": None,
            "human_notes": None,
        }

        try:
            pcm = _generate_pcm(
                model,
                text,
                voice_id,
                temperature=temperature,
                repetition_penalty=repetition_penalty,
                max_tokens=max_tokens,
            )
            pad_ms = _end_pad_ms_for_request(req, end_pad_ms, codes_end_pad_ms)
            out_name = f"{seg_id}__{voice_id}.wav"
            out_path = out_dir / out_name
            n_frames = _write_wav_pcm16_bytes(
                out_path, pcm, sample_rate, end_pad_ms=pad_ms
            )
            item["status"] = "EXECUTED"
            item["output"] = str(out_path)
            item["output_filename"] = out_name
            item["end_pad_ms"] = pad_ms
            item["num_samples"] = n_frames
            item["sample_rate"] = sample_rate
            item["duration_sec"] = round(n_frames / float(sample_rate), 3)
            report["ok_count"] += 1
        except Exception as exc:
            item["status"] = "FAILED"
            item["error"] = f"{type(exc).__name__}: {exc}"
            report["fail_count"] += 1

        report["segments"].append(item)
        print(
            json.dumps(
                {
                    "segment_id": item["segment_id"],
                    "speaker_id": item["speaker_id"],
                    "backend_voice_id": item["backend_voice_id"],
                    "status": item["status"],
                    "output_filename": item.get("output_filename"),
                    "spoken_text": item.get("spoken_text"),
                    "error": item.get("error"),
                },
                ensure_ascii=False,
            )
        )

    report_path = out_dir / "lab_render_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {report_path}", file=sys.stderr)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lab render: Orpheus ← Stage-2 synthesis manifest"
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--voice-map", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("lab_audio/orpheus_part1"))
    parser.add_argument("--use-display-text", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--model-name",
        default=None,
        help="HF model id (default from voice-map or finetune-prod)",
    )
    parser.add_argument("--max-model-len", type=int, default=2048)
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.6,
        help="Upstream: higher temperature can make speech faster",
    )
    parser.add_argument(
        "--repetition-penalty",
        type=float,
        default=1.3,
        help="Upstream requires >=1.1 for stability; higher may speak faster",
    )
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--end-pad-ms", type=int, default=250)
    parser.add_argument("--codes-end-pad-ms", type=int, default=550)
    args = parser.parse_args(argv)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        report = render_manifest(
            args.manifest,
            args.voice_map,
            out_dir,
            use_spoken_text=not args.use_display_text,
            limit=args.limit,
            model_name=args.model_name,
            max_model_len=args.max_model_len,
            temperature=args.temperature,
            repetition_penalty=args.repetition_penalty,
            max_tokens=args.max_tokens,
            end_pad_ms=args.end_pad_ms,
            codes_end_pad_ms=args.codes_end_pad_ms,
        )
    except SystemExit as exc:
        # Persist a failure report so notebook can show the real error
        fail_path = out_dir / "lab_render_report.json"
        fail = {
            "backend": "orpheus",
            "ok_count": 0,
            "fail_count": 1,
            "segments": [],
            "error": str(exc),
            "compatibility_notes": [
                "Render aborted before/during model load. "
                "On Colab prefer in-notebook render_manifest() after Cell 4 import "
                "(avoid os.system subprocess after CUDA init)."
            ],
        }
        fail_path.write_text(json.dumps(fail, ensure_ascii=False, indent=2) + "\n")
        print(f"Wrote failure report {fail_path}", file=sys.stderr)
        raise
    except Exception as exc:
        fail_path = out_dir / "lab_render_report.json"
        fail = {
            "backend": "orpheus",
            "ok_count": 0,
            "fail_count": 1,
            "segments": [],
            "error": f"{type(exc).__name__}: {exc}",
            "compatibility_notes": [
                "Unhandled exception during render. See error field."
            ],
        }
        fail_path.write_text(json.dumps(fail, ensure_ascii=False, indent=2) + "\n")
        print(f"Wrote failure report {fail_path}", file=sys.stderr)
        print(f"RENDER ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
