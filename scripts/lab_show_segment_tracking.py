#!/usr/bin/env python3
"""Print / export a per-segment tracking table for lab listening.

Use after lab_render_kokoro_from_manifest.py so you can verify each wav
against display_text / spoken_text without hunting through JSON by hand.

Examples:
  python scripts/lab_show_segment_tracking.py \\
    --report lab_audio/kokoro_part1/lab_render_report.json

  # On Colab, import show_tracking_html() from a notebook cell (see notebook).
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_rows(report: dict[str, Any], audio_dir: Path | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base = audio_dir or Path(report.get("segments", [{}])[0].get("output") or ".").parent
    for i, seg in enumerate(report.get("segments") or [], start=1):
        fname = seg.get("output_filename")
        if not fname and seg.get("output"):
            fname = Path(seg["output"]).name
        wav_path = (base / fname) if fname else None
        rows.append(
            {
                "index": i,
                "segment_id": seg.get("segment_id"),
                "event_id": seg.get("event_id"),
                "speaker_id": seg.get("speaker_id"),
                "backend_voice_id": seg.get("backend_voice_id"),
                "status": seg.get("status"),
                "duration_sec": seg.get("duration_sec"),
                "display_text": seg.get("display_text") or "",
                "spoken_text": seg.get("spoken_text") or "",
                "text_fed_to_tts": seg.get("text_fed_to_tts")
                or seg.get("spoken_text")
                or "",
                "protected_region_ids": seg.get("protected_region_ids") or [],
                "output_filename": fname,
                "wav_path": str(wav_path) if wav_path else None,
                "error": seg.get("error"),
            }
        )
    return rows


def print_text_table(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        print("=" * 72)
        print(
            f"[{row['index']}] {row['segment_id']} | speaker={row['speaker_id']} | "
            f"voice={row['backend_voice_id']} | status={row['status']} | "
            f"file={row['output_filename']}"
        )
        if row.get("duration_sec") is not None:
            print(f"  duration_sec: {row['duration_sec']}")
        print(f"  DISPLAY (script gốc): {row['display_text']}")
        print(f"  SPOKEN  (Stage-2)   : {row['spoken_text']}")
        if row["text_fed_to_tts"] not in (row["spoken_text"], row["display_text"]):
            print(f"  FED TO TTS          : {row['text_fed_to_tts']}")
        if row.get("protected_region_ids"):
            print(f"  protected           : {row['protected_region_ids']}")
        if row.get("error"):
            print(f"  ERROR               : {row['error']}")
        print("  human_content_match : (yes / partial / no)")
        print("  human_notes         :")
    print("=" * 72)


def build_html(rows: list[dict[str, Any]], title: str = "Segment tracking") -> str:
    """HTML table with embedded audio players for Colab/Jupyter display."""
    parts = [
        f"<h3>{html.escape(title)}</h3>",
        "<p>Nghe từng dòng và so với <b>DISPLAY</b> (script) / <b>SPOKEN</b> "
        "(text đưa TTS sau Stage-2). Điền match: yes | partial | no.</p>",
        "<table border='1' cellpadding='8' cellspacing='0' "
        "style='border-collapse:collapse;max-width:100%;font-family:sans-serif;font-size:14px'>",
        "<thead><tr style='background:#eee'>"
        "<th>#</th><th>segment</th><th>speaker / voice</th>"
        "<th>display_text (script)</th><th>spoken_text (fed if Stage-2)</th>"
        "<th>audio</th><th>status</th><th>content_match?</th><th>notes</th>"
        "</tr></thead><tbody>",
    ]
    for row in rows:
        audio_cell = ""
        if row.get("wav_path") and Path(row["wav_path"]).is_file():
            # relative path works in Colab if cwd is repo root
            src = html.escape(row["wav_path"])
            audio_cell = f'<audio controls preload="none" src="{src}"></audio><br><code>{html.escape(row.get("output_filename") or "")}</code>'
        elif row.get("output_filename"):
            audio_cell = f"<code>{html.escape(row['output_filename'])}</code> (file missing?)"
        else:
            audio_cell = "—"

        parts.append(
            "<tr>"
            f"<td>{row['index']}</td>"
            f"<td><code>{html.escape(str(row['segment_id']))}</code></td>"
            f"<td>{html.escape(str(row['speaker_id']))}<br>"
            f"<code>{html.escape(str(row['backend_voice_id']))}</code></td>"
            f"<td style='max-width:220px'>{html.escape(row['display_text'])}</td>"
            f"<td style='max-width:220px'>{html.escape(row['spoken_text'])}</td>"
            f"<td>{audio_cell}</td>"
            f"<td>{html.escape(str(row['status']))}</td>"
            f"<td style='min-width:90px'><i>yes/partial/no</i></td>"
            f"<td style='min-width:120px'></td>"
            "</tr>"
        )
    parts.append("</tbody></table>")
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show per-segment lab tracking table")
    parser.add_argument(
        "--report",
        type=Path,
        required=True,
        help="lab_render_report.json from lab renderer",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=None,
        help="Directory containing wav files (default: report's parent)",
    )
    parser.add_argument(
        "--html-out",
        type=Path,
        default=None,
        help="Optional path to write HTML tracking page",
    )
    args = parser.parse_args(argv)

    report = load_report(args.report)
    audio_dir = args.audio_dir or args.report.parent
    rows = build_rows(report, audio_dir=audio_dir)
    print_text_table(rows)

    if args.html_out:
        args.html_out.write_text(
            build_html(rows, title=f"Tracking: {report.get('transcript_id')}"),
            encoding="utf-8",
        )
        print(f"Wrote HTML {args.html_out}", file=__import__("sys").stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
