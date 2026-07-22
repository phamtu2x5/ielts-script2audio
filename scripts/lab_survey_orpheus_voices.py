#!/usr/bin/env python3
"""Lab: same Stage-2 lines × many Orpheus fixed voice names.

Uses local OrpheusModel (orpheus-speech + vLLM), not paid API.

Example:
  python scripts/lab_survey_orpheus_voices.py \\
    --manifest outputs/part1_manifest.json \\
    --inventory configs/voice_maps/orpheus_voice_inventory.json \\
    --preset en_shortlist \\
    --out-dir lab_audio/orpheus_voice_survey \\
    --event-ids e004,e006,e008,e011
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lab_survey_kokoro_voices import _lines_from_manifest  # noqa: E402


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_wav_pcm16_bytes(
    path: Path, pcm_bytes: bytes, sample_rate: int = 24000, *, end_pad_ms: int = 400
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n_pad = int(sample_rate * max(0, end_pad_ms) / 1000)
    pad = b"\x00\x00" * n_pad
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes + pad)


def _voices(
    inventory: dict[str, Any], preset: str | None, voice_ids: list[str] | None
) -> list[str]:
    if voice_ids:
        return voice_ids
    if preset:
        p = (inventory.get("lab_presets") or {}).get(preset)
        if not p:
            known = ", ".join(sorted((inventory.get("lab_presets") or {})))
            raise SystemExit(f"unknown preset {preset!r}; known: {known}")
        return list(p.get("voice_ids") or [])
    return [v["id"] for v in (inventory.get("voices") or []) if v.get("id")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Survey Orpheus voices on Stage-2 lines")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("configs/voice_maps/orpheus_voice_inventory.json"),
    )
    parser.add_argument("--out-dir", type=Path, default=Path("lab_audio/orpheus_voice_survey"))
    parser.add_argument("--preset", default="en_shortlist")
    parser.add_argument("--voices", default=None, help="Comma-separated; overrides preset")
    parser.add_argument("--event-ids", default="e004,e006,e008,e011")
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--max-model-len", type=int, default=2048)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--repetition-penalty", type=float, default=1.3)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--end-pad-ms", type=int, default=450)
    args = parser.parse_args(argv)

    try:
        from orpheus_tts import OrpheusModel
    except ImportError as exc:
        raise SystemExit(
            "Install local stack: pip install orpheus-speech\n"
            "If vLLM breaks: pip install vllm==0.7.3\n"
            "Do NOT use pip install orpheus-tts (paid API client).\n"
            f"Original error: {exc}"
        ) from exc

    manifest = _load_json(args.manifest)
    inventory = _load_json(args.inventory)
    model_id = (
        args.model_name
        or inventory.get("model_name")
        or "canopylabs/orpheus-tts-0.1-finetune-prod"
    )
    voice_ids = (
        [v.strip() for v in args.voices.split(",") if v.strip()] if args.voices else None
    )
    voices = _voices(inventory, None if voice_ids else args.preset, voice_ids)
    event_ids = (
        [e.strip() for e in args.event_ids.split(",") if e.strip()]
        if args.event_ids.strip()
        else None
    )
    lines = _lines_from_manifest(manifest, event_ids, None)
    if not lines:
        raise SystemExit("no lines from manifest")
    if not voices:
        raise SystemExit("no voices selected")

    print(f"Loading {model_id} ...", file=sys.stderr)
    model = OrpheusModel(model_name=model_id, max_model_len=args.max_model_len)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "backend": "orpheus",
        "model_name": model_id,
        "preset": None if voice_ids else args.preset,
        "voices": voices,
        "transcript_id": manifest.get("transcript_id"),
        "temperature": args.temperature,
        "repetition_penalty": args.repetition_penalty,
        "lines": lines,
        "renders": [],
        "ok_count": 0,
        "fail_count": 0,
    }

    for voice in voices:
        for line in lines:
            eid = line.get("event_id") or "line"
            text = line.get("spoken_text") or line.get("display_text") or ""
            out_name = f"{voice}__{eid}.wav"
            item: dict[str, Any] = {
                "voice_id": voice,
                "event_id": eid,
                "speaker_id": line.get("speaker_id"),
                "display_text": line.get("display_text"),
                "spoken_text": line.get("spoken_text"),
                "text_fed_to_tts": text,
                "output_filename": out_name,
                "status": "PENDING",
                "error": None,
            }
            try:
                chunks: list[bytes] = []
                for audio_chunk in model.generate_speech(
                    prompt=text,
                    voice=voice,
                    temperature=args.temperature,
                    repetition_penalty=args.repetition_penalty,
                    max_tokens=args.max_tokens,
                ):
                    if audio_chunk is None:
                        continue
                    if isinstance(audio_chunk, (bytes, bytearray)):
                        chunks.append(bytes(audio_chunk))
                    elif hasattr(audio_chunk, "tobytes"):
                        chunks.append(audio_chunk.tobytes())
                    else:
                        chunks.append(bytes(audio_chunk))
                if not chunks:
                    raise RuntimeError("no audio chunks")
                pcm = b"".join(chunks)
                _write_wav_pcm16_bytes(
                    out_dir / out_name, pcm, 24000, end_pad_ms=args.end_pad_ms
                )
                item["status"] = "EXECUTED"
                report["ok_count"] += 1
            except Exception as exc:
                item["status"] = "FAILED"
                item["error"] = f"{type(exc).__name__}: {exc}"
                report["fail_count"] += 1
            report["renders"].append(item)
            print(
                json.dumps(
                    {
                        "voice": voice,
                        "event_id": eid,
                        "status": item["status"],
                        "file": out_name,
                        "error": item.get("error"),
                    },
                    ensure_ascii=False,
                )
            )

    report_path = out_dir / "voice_survey_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {report_path}", file=sys.stderr)
    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
