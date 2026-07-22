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
import re
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


def _write_wav_pcm16(
    path: Path,
    audio,
    sample_rate: int,
    *,
    end_pad_ms: int = 0,
) -> None:
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(audio, dtype=np.float32).reshape(-1)
    # clip
    arr = np.clip(arr, -1.0, 1.0)
    pad_ms = max(0, int(end_pad_ms))
    if pad_ms > 0:
        # Trailing silence so the last phoneme is not cut off by the engine/player.
        # This does NOT re-speak content (unlike repeating the last letter/digit).
        n_pad = int(sample_rate * pad_ms / 1000)
        if n_pad > 0:
            arr = np.concatenate([arr, np.zeros(n_pad, dtype=np.float32)])
    pcm = (arr * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def _end_pad_ms_for_request(req: dict[str, Any], default_ms: int, codes_ms: int) -> int:
    """Extra tail silence for code-like / protected segments."""
    protected = req.get("protected_region_ids") or []
    spoken = (req.get("spoken_text") or "").lower()
    # Heuristic: paced letter/digit chains from Stage-2 codes
    looks_like_code = (
        "..." in (req.get("spoken_text") or "")
        and any(
            token in spoken
            for token in (
                " zero",
                " one",
                " two",
                " three",
                " four",
                " five",
                " six",
                " seven",
                " eight",
                " nine",
            )
        )
    )
    # single-letter chains: "t... h... o"
    letter_chain = bool(re.search(r"\b[A-Z](?:\.\.\. [A-Z]){2,}\b", req.get("spoken_text") or ""))
    if protected or looks_like_code or letter_chain:
        return max(default_ms, codes_ms)
    return default_ms


def render_manifest(
    manifest_path: Path,
    voice_map_path: Path,
    out_dir: Path,
    *,
    use_spoken_text: bool = True,
    limit: int | None = None,
    end_pad_ms: int = 250,
    codes_end_pad_ms: int = 550,
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
    # requests may omit event_id; join from segments[] for tracking
    event_by_segment = {
        s.get("segment_id"): s.get("event_id")
        for s in (manifest.get("segments") or [])
        if s.get("segment_id")
    }
    if limit is not None:
        requests = requests[:limit]

    # One pipeline per lang_code used
    pipelines: dict[str, Any] = {}
    report: dict[str, Any] = {
        "manifest_id": manifest.get("manifest_id"),
        "transcript_id": manifest.get("transcript_id"),
        "backend": "kokoro",
        "text_field_used": "spoken_text" if use_spoken_text else "display_text",
        "end_pad_ms_default": end_pad_ms,
        "codes_end_pad_ms": codes_end_pad_ms,
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
            "event_id": req.get("event_id") or event_by_segment.get(seg_id),
            "speaker_id": req.get("speaker_id"),
            "voice_profile_id": vp,
            "backend_voice_id": voice_id,
            "lang_code": lang_code,
            # Full texts for human tracking (do not truncate — needed to verify content)
            "display_text": req.get("display_text") or "",
            "spoken_text": req.get("spoken_text") or "",
            "text_fed_to_tts": text,
            "text_field_used": "spoken_text" if use_spoken_text else "display_text",
            "protected_region_ids": list(req.get("protected_region_ids") or []),
            "status": "PENDING",
            "output": None,
            "output_filename": None,
            "error": None,
            # Filled by human in notebook / tracking sheet
            "human_content_match": None,
            "human_notes": None,
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
            out_name = f"{seg_id}__{voice_id}.wav"
            out_path = out_dir / out_name
            pad_ms = _end_pad_ms_for_request(req, end_pad_ms, codes_end_pad_ms)
            _write_wav_pcm16(
                out_path,
                audio_out,
                sample_rate,
                end_pad_ms=pad_ms,
            )
            item["status"] = "EXECUTED"
            item["output"] = str(out_path)
            item["output_filename"] = out_name
            item["end_pad_ms"] = pad_ms
            # duration includes pad (what is on disk)
            n_samples = int(audio_out.shape[0]) + int(sample_rate * pad_ms / 1000)
            item["num_samples"] = n_samples
            item["sample_rate"] = sample_rate
            item["duration_sec"] = round(float(n_samples) / float(sample_rate), 3)
            report["ok_count"] += 1
        except Exception as exc:  # lab must record failures honestly
            item["status"] = "FAILED"
            item["error"] = f"{type(exc).__name__}: {exc}"
            report["fail_count"] += 1

        report["segments"].append(item)
        # stdout: one compact line per segment for live tracking
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
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Human-readable tracking sheet (CSV) — open in Sheets / Excel / notebook
    tracking_csv = out_dir / "segment_tracking.csv"
    _write_tracking_csv(tracking_csv, report["segments"])

    # Empty review template for human marks (content match per line)
    review_path = out_dir / "segment_review_template.json"
    _write_review_template(review_path, report["segments"])

    print(f"Wrote {report_path}", file=sys.stderr)
    print(f"Wrote {tracking_csv}", file=sys.stderr)
    print(f"Wrote {review_path}", file=sys.stderr)
    return report


def _write_tracking_csv(path: Path, segments: list[dict[str, Any]]) -> None:
    import csv

    fields = [
        "segment_id",
        "event_id",
        "speaker_id",
        "backend_voice_id",
        "status",
        "output_filename",
        "duration_sec",
        "display_text",
        "spoken_text",
        "text_fed_to_tts",
        "protected_region_ids",
        "error",
        "human_content_match",
        "human_notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for seg in segments:
            row = {k: seg.get(k) for k in fields}
            # CSV-friendly list
            pr = row.get("protected_region_ids") or []
            row["protected_region_ids"] = "|".join(pr) if isinstance(pr, list) else pr
            writer.writerow(row)


def _write_review_template(path: Path, segments: list[dict[str, Any]]) -> None:
    """Template for human marks: content_match = yes | partial | no | skip."""
    rows = []
    for seg in segments:
        rows.append(
            {
                "segment_id": seg.get("segment_id"),
                "output_filename": seg.get("output_filename"),
                "speaker_id": seg.get("speaker_id"),
                "display_text": seg.get("display_text"),
                "spoken_text": seg.get("spoken_text"),
                "text_fed_to_tts": seg.get("text_fed_to_tts"),
                # Fill after listening:
                "content_match": "",  # yes | partial | no | skip
                "matches_display_or_spoken": "",  # display | spoken | both | neither
                "issues": [],  # e.g. "wrong words", "missing spelling", "wrong speaker"
                "notes": "",
            }
        )
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    parser.add_argument(
        "--end-pad-ms",
        type=int,
        default=250,
        help="Trailing silence (ms) appended to every segment wav",
    )
    parser.add_argument(
        "--codes-end-pad-ms",
        type=int,
        default=550,
        help="Trailing silence (ms) for protected/code-like segments (spelling/postcode/phone)",
    )
    args = parser.parse_args(argv)

    report = render_manifest(
        args.manifest,
        args.voice_map,
        args.out_dir,
        use_spoken_text=not args.use_display_text,
        limit=args.limit,
        end_pad_ms=args.end_pad_ms,
        codes_end_pad_ms=args.codes_end_pad_ms,
    )
    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
