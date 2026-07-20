"""CLI prepare command tests."""

from __future__ import annotations

import json
from pathlib import Path

from ielts_script2audio.cli import main

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_cli_prepare_stdout(capsys):
    code = main(["prepare", str(EXAMPLES / "part1_valid.json")])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["transcript_id"] == "ex-part1-valid-001"
    assert payload["step_status"]["render"] == "NOT_EXECUTED"
    assert len(payload["requests"]) == len(payload["segments"])


def test_cli_prepare_to_file(tmp_path):
    out = tmp_path / "manifest.json"
    code = main(
        [
            "prepare",
            str(EXAMPLES / "part1_valid.json"),
            "-o",
            str(out),
            "--pretty",
        ]
    )
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "stage2.v1"


def test_cli_prepare_invalid_exit_code(capsys):
    code = main(["prepare", str(EXAMPLES / "part1_invalid_speaker_count.json")])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["validation"]["valid"] is False
