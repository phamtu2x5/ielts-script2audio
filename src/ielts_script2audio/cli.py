"""CLI for Stage 1 validate + Stage 2 prepare (no TTS render)."""

from __future__ import annotations

import argparse
import json
import sys

from ielts_script2audio.models.input_transcript import PartNumber
from ielts_script2audio.models.validation import ValidationReport
from ielts_script2audio.pipeline.prepare import prepare_path
from ielts_script2audio.validation.transcript import load_and_validate_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ielts-s2a",
        description=(
            "IELTS Script-to-Audio control-plane CLI. "
            "Validates transcripts and builds provider-neutral synthesis manifests. "
            "Does not render audio or call any TTS provider."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate_p = sub.add_parser(
        "validate",
        help="Validate a structured InputTranscript JSON file",
    )
    validate_p.add_argument("path", help="Path to transcript JSON")
    validate_p.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print ValidationReport JSON",
    )

    prepare_p = sub.add_parser(
        "prepare",
        help=(
            "Validate + normalise + risk + segment + emit TTS-neutral synthesis manifest"
        ),
    )
    prepare_p.add_argument("path", help="Path to transcript JSON")
    prepare_p.add_argument(
        "-o",
        "--output",
        help="Write manifest JSON to this path (default: stdout)",
    )
    prepare_p.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON",
    )
    prepare_p.add_argument(
        "--allow-invalid",
        action="store_true",
        help="Emit manifest even if validation has errors (still lists blocking_issues)",
    )
    return parser


def _print_json(payload: dict, *, pretty: bool) -> None:
    indent = 2 if pretty else None
    print(json.dumps(payload, ensure_ascii=False, indent=indent))


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    pretty = bool(getattr(args, "pretty", False))

    if args.command == "validate":
        _transcript, report, schema_issues = load_and_validate_path(args.path)
        if schema_issues:
            failed = ValidationReport(
                transcript_id="unknown",
                part=PartNumber.PART_1,
                valid=False,
                issues=schema_issues,
                utterance_count=0,
                answer_bearing_span_count=0,
            )
            _print_json(failed.model_dump(mode="json"), pretty=pretty)
            return 2
        assert report is not None
        _print_json(report.model_dump(mode="json"), pretty=pretty)
        return 0 if report.valid else 1

    if args.command == "prepare":
        manifest, schema_issues = prepare_path(args.path)
        if schema_issues or manifest is None:
            failed = ValidationReport(
                transcript_id="unknown",
                part=PartNumber.PART_1,
                valid=False,
                issues=schema_issues,
                utterance_count=0,
                answer_bearing_span_count=0,
            )
            _print_json(
                {
                    "error": "schema_or_io_failure",
                    "validation": failed.model_dump(mode="json"),
                },
                pretty=pretty,
            )
            return 2

        payload = manifest.model_dump(mode="json")
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                indent = 2 if pretty else None
                json.dump(payload, fh, ensure_ascii=False, indent=indent)
                fh.write("\n")
        else:
            _print_json(payload, pretty=pretty)

        if not manifest.validation.valid and not args.allow_invalid:
            return 1
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
