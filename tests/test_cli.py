"""CLI smoke tests for Stage 1 validate command."""

from __future__ import annotations

import json
from pathlib import Path

from ielts_script2audio.cli import main

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_cli_validate_success(capsys):
    code = main(["validate", str(EXAMPLES / "part1_valid.json")])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["step_status"] == "EXECUTED"


def test_cli_validate_failure(capsys):
    code = main(["validate", str(EXAMPLES / "part1_invalid_speaker_count.json")])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
