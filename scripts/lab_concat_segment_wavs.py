#!/usr/bin/env python3
"""Concatenate lab segment WAVs into one continuous file.

Default gap mode is **adaptive** (not a single fixed silence for every cut):
  - same speaker continuing  → short gap
  - speaker change (turn)    → longer gap
  - after a long segment     → slightly longer breathe

Does not re-run TTS. Does not edit transcript script.

Example:
  python scripts/lab_concat_segment_wavs.py \\
    --report lab_audio/kokoro_part1/lab_render_report.json \\
    --out lab_audio/kokoro_part1/part1_full.wav \\
    --gap-mode adaptive
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path
from typing import Any


def _read_wav_mono_int16(path: Path) -> tuple[list[int], int]:
    with wave.open(str(path), "rb") as wf:
        nch = wf.getnchannels()
        sw = wf.getsampwidth()
        rate = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)
    if sw != 2:
        raise ValueError(f"{path}: expected 16-bit PCM, got sample width {sw}")
    import array

    samples = array.array("h")
    samples.frombytes(raw)
    if nch == 1:
        return list(samples), rate
    if nch != 2:
        raise ValueError(f"{path}: unsupported channels={nch}")
    mono = []
    for i in range(0, len(samples), 2):
        mono.append(int((samples[i] + samples[i + 1]) / 2))
    return mono, rate


def _write_wav_mono_int16(path: Path, samples: list[int], rate: int) -> None:
    import array

    path.parent.mkdir(parents=True, exist_ok=True)
    arr = array.array("h", samples)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(arr.tobytes())


def _adaptive_gap_ms(
    *,
    prev_speaker: str | None,
    cur_speaker: str | None,
    prev_duration_sec: float | None,
    base_same_ms: int,
    base_turn_ms: int,
) -> int:
    """Choose silence before current segment based on turn-taking context."""
    if prev_speaker is None:
        return 0
    if prev_speaker != cur_speaker:
        gap = base_turn_ms
    else:
        gap = base_same_ms
    # After a long turn, leave a touch more air (dialogue breathe)
    if prev_duration_sec is not None and prev_duration_sec >= 3.5:
        gap += 120
    elif prev_duration_sec is not None and prev_duration_sec >= 2.2:
        gap += 60
    # Small jitter-free clamp
    return max(80, min(gap, 1200))


def concat_from_report(
    report_path: Path,
    out_path: Path,
    *,
    gap_mode: str = "adaptive",
    gap_ms: int | None = None,
    same_speaker_gap_ms: int = 220,
    turn_gap_ms: int = 520,
    audio_dir: Path | None = None,
) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    base = audio_dir or report_path.parent

    combined: list[int] = []
    rate: int | None = None
    used: list[str] = []
    skipped: list[str] = []
    gap_log: list[dict[str, Any]] = []

    prev_speaker: str | None = None
    prev_duration: float | None = None

    for seg in report.get("segments") or []:
        if seg.get("status") != "EXECUTED":
            skipped.append(str(seg.get("segment_id")))
            continue
        fname = seg.get("output_filename")
        if not fname and seg.get("output"):
            fname = Path(seg["output"]).name
        if not fname:
            skipped.append(str(seg.get("segment_id")))
            continue
        path = base / fname
        if not path.is_file():
            skipped.append(str(seg.get("segment_id")))
            continue
        samples, r = _read_wav_mono_int16(path)
        if rate is None:
            rate = r
        elif r != rate:
            raise SystemExit(
                f"sample rate mismatch: {path} has {r} Hz, expected {rate} Hz"
            )

        cur_speaker = seg.get("speaker_id")
        if gap_mode == "fixed":
            # Legacy single gap for every boundary
            fixed = 450 if gap_ms is None else max(0, int(gap_ms))
            gap = 0 if prev_speaker is None else fixed
        else:
            gap = _adaptive_gap_ms(
                prev_speaker=prev_speaker,
                cur_speaker=cur_speaker,
                prev_duration_sec=prev_duration,
                base_same_ms=same_speaker_gap_ms,
                base_turn_ms=turn_gap_ms,
            )

        if combined and gap > 0 and rate:
            combined.extend([0] * int(rate * gap / 1000))
        combined.extend(samples)
        used.append(fname)
        gap_log.append(
            {
                "segment_id": seg.get("segment_id"),
                "speaker_id": cur_speaker,
                "gap_before_ms": gap,
                "reason": (
                    "start"
                    if prev_speaker is None
                    else (
                        "turn_change"
                        if prev_speaker != cur_speaker
                        else "same_speaker"
                    )
                ),
            }
        )
        prev_speaker = cur_speaker
        # prefer measured duration from samples
        prev_duration = len(samples) / float(rate) if rate else seg.get("duration_sec")

    if rate is None or not combined:
        raise SystemExit("no EXECUTED wav segments to concatenate")

    _write_wav_mono_int16(out_path, combined, rate)
    meta = {
        "output": str(out_path),
        "sample_rate": rate,
        "gap_mode": gap_mode,
        "same_speaker_gap_ms": same_speaker_gap_ms if gap_mode == "adaptive" else None,
        "turn_gap_ms": turn_gap_ms if gap_mode == "adaptive" else None,
        "fixed_gap_ms": gap_ms if gap_mode == "fixed" else None,
        "num_segments_used": len(used),
        "segments_used": used,
        "segments_skipped": skipped,
        "gaps": gap_log,
        "duration_sec": round(len(combined) / rate, 3),
        "transcript_id": report.get("transcript_id"),
    }
    meta_path = out_path.with_suffix(".concat.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Concatenate lab segment WAVs")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--gap-mode",
        choices=("adaptive", "fixed"),
        default="adaptive",
        help="adaptive (default): shorter within speaker, longer on turn change; fixed: one gap",
    )
    parser.add_argument(
        "--gap-ms",
        type=int,
        default=None,
        help="Only for --gap-mode fixed (default 450 if omitted)",
    )
    parser.add_argument(
        "--same-speaker-gap-ms",
        type=int,
        default=220,
        help="Adaptive: silence when same speaker continues",
    )
    parser.add_argument(
        "--turn-gap-ms",
        type=int,
        default=520,
        help="Adaptive: silence when speaker changes",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=None,
        help="Directory of wavs (default: report parent)",
    )
    args = parser.parse_args(argv)
    meta = concat_from_report(
        args.report,
        args.out,
        gap_mode=args.gap_mode,
        gap_ms=args.gap_ms,
        same_speaker_gap_ms=args.same_speaker_gap_ms,
        turn_gap_ms=args.turn_gap_ms,
        audio_dir=args.audio_dir,
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
