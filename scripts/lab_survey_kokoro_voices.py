#!/usr/bin/env python3
"""Lab: render the same Stage-2 lines with many Kokoro fixed voice IDs.

Purpose
-------
Compare intelligibility / naturalness across Kokoro voices while reusing
manifest spoken_text (Stage 1–2 contract). Not production casting.

Example (British full set):
  python scripts/lab_survey_kokoro_voices.py \\
    --manifest outputs/part1_manifest.json \\
    --inventory configs/voice_maps/kokoro_voice_inventory.json \\
    --preset gb_core \\
    --out-dir lab_audio/kokoro_voice_survey \\
    --event-ids e004,e006,e008,e011

Does not edit transcript script / display_text.
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


def _write_wav_pcm16(
    path: Path,
    audio,
    sample_rate: int,
    *,
    end_pad_ms: int = 400,
) -> None:
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(audio, dtype=np.float32).reshape(-1)
    arr = np.clip(arr, -1.0, 1.0)
    if end_pad_ms > 0:
        n_pad = int(sample_rate * end_pad_ms / 1000)
        if n_pad > 0:
            arr = np.concatenate([arr, np.zeros(n_pad, dtype=np.float32)])
    pcm = (arr * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def _lines_from_manifest(
    manifest: dict[str, Any],
    event_ids: list[str] | None,
    max_lines: int | None,
) -> list[dict[str, Any]]:
    """Pick stable lines: prefer prepared_utterances, fallback requests."""
    lines: list[dict[str, Any]] = []
    prepared = manifest.get("prepared_utterances") or []
    if prepared:
        for u in prepared:
            eid = u.get("event_id")
            if event_ids and eid not in event_ids:
                continue
            lines.append(
                {
                    "event_id": eid,
                    "speaker_id": u.get("speaker_id"),
                    "display_text": u.get("display_text") or "",
                    "spoken_text": u.get("spoken_text") or "",
                    "protected_region_ids": list(u.get("protected_region_ids") or []),
                }
            )
    else:
        for req in manifest.get("requests") or []:
            lines.append(
                {
                    "event_id": req.get("segment_id"),
                    "speaker_id": req.get("speaker_id"),
                    "display_text": req.get("display_text") or "",
                    "spoken_text": req.get("spoken_text") or "",
                    "protected_region_ids": list(req.get("protected_region_ids") or []),
                }
            )
        if event_ids:
            lines = [ln for ln in lines if ln["event_id"] in event_ids]

    if max_lines is not None:
        lines = lines[: max(0, int(max_lines))]
    return lines


def _resolve_voice_list(
    inventory: dict[str, Any],
    *,
    preset: str | None,
    voice_ids: list[str] | None,
    locale: str,
) -> tuple[str, list[str]]:
    """Return (lang_code, voice_id list)."""
    locales = inventory.get("locales") or {}
    loc = locales.get(locale) or {}
    lang_code = loc.get("lang_code") or ("b" if locale == "en-GB" else "a")

    if voice_ids:
        return lang_code, voice_ids

    if preset:
        presets = inventory.get("lab_presets") or {}
        p = presets.get(preset)
        if not p:
            known = ", ".join(sorted(presets))
            raise SystemExit(f"unknown preset {preset!r}; known: {known}")
        # preset may override locale
        preset_locale = p.get("locale") or locale
        loc = locales.get(preset_locale) or loc
        lang_code = loc.get("lang_code") or lang_code
        return lang_code, list(p.get("voice_ids") or [])

    # default: all voices in locale
    return lang_code, [v["id"] for v in (loc.get("voices") or []) if v.get("id")]


def survey(
    manifest_path: Path,
    inventory_path: Path,
    out_dir: Path,
    *,
    preset: str | None = "gb_core",
    voice_ids: list[str] | None = None,
    locale: str = "en-GB",
    event_ids: list[str] | None = None,
    max_lines: int | None = None,
    end_pad_ms: int = 450,
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
    inventory = _load_json(inventory_path)
    lang_code, voices = _resolve_voice_list(
        inventory, preset=preset, voice_ids=voice_ids, locale=locale
    )
    if not voices:
        raise SystemExit("no voices selected")

    lines = _lines_from_manifest(manifest, event_ids, max_lines)
    if not lines:
        raise SystemExit("no lines selected from manifest")

    out_dir.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code=lang_code)

    report: dict[str, Any] = {
        "backend": "kokoro",
        "lang_code": lang_code,
        "locale": locale,
        "preset": preset,
        "voices": voices,
        "manifest_id": manifest.get("manifest_id"),
        "transcript_id": manifest.get("transcript_id"),
        "end_pad_ms": end_pad_ms,
        "lines": lines,
        "renders": [],
        "ok_count": 0,
        "fail_count": 0,
    }

    for voice_id in voices:
        for line in lines:
            eid = line["event_id"] or "line"
            text = line["spoken_text"] or line["display_text"]
            safe_voice = re.sub(r"[^\w\-]+", "_", voice_id)
            out_name = f"{safe_voice}__{eid}.wav"
            out_path = out_dir / out_name
            item: dict[str, Any] = {
                "voice_id": voice_id,
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
                chunks: list[Any] = []
                sample_rate = 24000
                for result in pipeline(text, voice=voice_id):
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
                    raise RuntimeError("Kokoro returned no audio chunks")
                audio_out = np.concatenate(chunks)
                _write_wav_pcm16(
                    out_path, audio_out, sample_rate, end_pad_ms=end_pad_ms
                )
                item["status"] = "EXECUTED"
                item["sample_rate"] = sample_rate
                item["duration_sec"] = round(
                    (audio_out.shape[0] + int(sample_rate * end_pad_ms / 1000))
                    / float(sample_rate),
                    3,
                )
                report["ok_count"] += 1
            except Exception as exc:
                item["status"] = "FAILED"
                item["error"] = f"{type(exc).__name__}: {exc}"
                report["fail_count"] += 1

            report["renders"].append(item)
            print(
                json.dumps(
                    {
                        "voice_id": voice_id,
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
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Survey many Kokoro voices on the same Stage-2 lines"
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("configs/voice_maps/kokoro_voice_inventory.json"),
    )
    parser.add_argument("--out-dir", type=Path, default=Path("lab_audio/kokoro_voice_survey"))
    parser.add_argument(
        "--preset",
        default="gb_core",
        help="Inventory lab_presets key (gb_core, gb_shortlist, us_sample) or empty with --voices",
    )
    parser.add_argument(
        "--voices",
        default=None,
        help="Comma-separated voice ids (overrides preset)",
    )
    parser.add_argument("--locale", default="en-GB")
    parser.add_argument(
        "--event-ids",
        default="e004,e006,e008,e011",
        help="Comma-separated event_ids from manifest (empty = all)",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=None,
        help="Cap number of lines (after event-id filter)",
    )
    parser.add_argument("--end-pad-ms", type=int, default=450)
    parser.add_argument(
        "--no-preset",
        action="store_true",
        help="Ignore preset; use all voices in --locale",
    )
    args = parser.parse_args(argv)

    voice_ids = (
        [v.strip() for v in args.voices.split(",") if v.strip()]
        if args.voices
        else None
    )
    event_ids = (
        [e.strip() for e in args.event_ids.split(",") if e.strip()]
        if args.event_ids is not None and args.event_ids.strip() != ""
        else None
    )
    preset = None if args.no_preset or voice_ids else args.preset

    report = survey(
        args.manifest,
        args.inventory,
        args.out_dir,
        preset=preset,
        voice_ids=voice_ids,
        locale=args.locale,
        event_ids=event_ids,
        max_lines=args.max_lines,
        end_pad_ms=args.end_pad_ms,
    )
    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
