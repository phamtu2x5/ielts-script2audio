#!/usr/bin/env python3
"""Concatenate lab segment WAVs into one continuous file (with silence gaps).

Uses segment order from lab_render_report.json (Stage-2 request order).
Does not re-run TTS. Does not edit transcript script.

Example:
  python scripts/lab_concat_segment_wavs.py \\
    --report lab_audio/kokoro_part1/lab_render_report.json \\
    --out lab_audio/kokoro_part1/part1_full.wav \\
    --gap-ms 450
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
    # Interleaved int16
    import array

    samples = array.array("h")
    samples.frombytes(raw)
    if nch == 1:
        return list(samples), rate
    if nch != 2:
        raise ValueError(f"{path}: unsupported channels={nch}")
    # downmix stereo → mono
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


def concat_from_report(
    report_path: Path,
    out_path: Path,
    *,
    gap_ms: int = 450,
    audio_dir: Path | None = None,
) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    base = audio_dir or report_path.parent
    gap_ms = max(0, int(gap_ms))

    combined: list[int] = []
    rate: int | None = None
    used: list[str] = []
    skipped: list[str] = []

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
        if combined and gap_ms:
            combined.extend([0] * int(rate * gap_ms / 1000))
        combined.extend(samples)
        used.append(fname)

    if rate is None or not combined:
        raise SystemExit("no EXECUTED wav segments to concatenate")

    _write_wav_mono_int16(out_path, combined, rate)
    meta = {
        "output": str(out_path),
        "sample_rate": rate,
        "gap_ms": gap_ms,
        "num_segments_used": len(used),
        "segments_used": used,
        "segments_skipped": skipped,
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
    parser.add_argument("--gap-ms", type=int, default=450, help="Silence between segments")
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
        gap_ms=args.gap_ms,
        audio_dir=args.audio_dir,
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
