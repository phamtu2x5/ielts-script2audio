"""Unit tests for Stage 1 transcript validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ielts_script2audio.models.input_transcript import (
    AnswerBearingSpan,
    DeliveryProfile,
    InputTranscript,
    PartNumber,
    Speaker,
    SpeakerRole,
    Utterance,
)
from ielts_script2audio.validation.transcript import (
    load_and_validate_path,
    validate_transcript,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def _utt(event_id: str, speaker_id: str, text: str) -> Utterance:
    return Utterance(event_id=event_id, speaker_id=speaker_id, display_text=text)


def _part1_base(**kwargs) -> InputTranscript:
    data = dict(
        transcript_id="t1",
        part=PartNumber.PART_1,
        speakers=[
            Speaker(speaker_id="a", role=SpeakerRole.CONTENT),
            Speaker(speaker_id="b", role=SpeakerRole.CONTENT),
        ],
        utterances=[
            _utt("e1", "a", "Hello."),
            _utt("e2", "b", "Hi there."),
        ],
    )
    data.update(kwargs)
    return InputTranscript(**data)


def test_part1_valid_minimal():
    report = validate_transcript(_part1_base())
    assert report.valid is True
    assert report.error_count == 0
    assert report.speaker_map is not None
    assert report.speaker_map.content_speaker_count == 2
    assert report.speaker_map.narrator_voice_count == 0
    assert report.utterance_count == 2
    assert report.step_status.value == "EXECUTED"


def test_part1_rejects_one_content_speaker():
    t = InputTranscript(
        transcript_id="bad",
        part=PartNumber.PART_1,
        speakers=[Speaker(speaker_id="a", role=SpeakerRole.CONTENT)],
        utterances=[_utt("e1", "a", "Only one speaker.")],
    )
    report = validate_transcript(t)
    assert report.valid is False
    assert any(i.code == "invalid_content_speaker_count" for i in report.issues)


def test_part2_requires_exactly_one_content_speaker():
    ok = InputTranscript(
        transcript_id="p2",
        part=PartNumber.PART_2,
        speakers=[Speaker(speaker_id="g", role=SpeakerRole.CONTENT)],
        utterances=[_utt("e1", "g", "Welcome.")],
    )
    assert validate_transcript(ok).valid is True

    bad = InputTranscript(
        transcript_id="p2bad",
        part=PartNumber.PART_2,
        speakers=[
            Speaker(speaker_id="g", role=SpeakerRole.CONTENT),
            Speaker(speaker_id="x", role=SpeakerRole.CONTENT),
        ],
        utterances=[
            _utt("e1", "g", "Welcome."),
            _utt("e2", "x", "Should not be here."),
        ],
    )
    report = validate_transcript(bad)
    assert report.valid is False
    assert any(i.code == "invalid_content_speaker_count" for i in report.issues)


@pytest.mark.parametrize(
    ("count", "expect_valid"),
    [
        (1, False),
        (2, True),
        (3, True),
        (4, True),
        (5, False),
    ],
)
def test_part3_content_speaker_range(count: int, expect_valid: bool):
    speakers = [
        Speaker(speaker_id=f"s{i}", role=SpeakerRole.CONTENT) for i in range(count)
    ]
    utterances = [_utt(f"e{i}", f"s{i}", f"Line {i}.") for i in range(count)]
    t = InputTranscript(
        transcript_id="p3",
        part=PartNumber.PART_3,
        speakers=speakers,
        utterances=utterances,
    )
    assert validate_transcript(t).valid is expect_valid


def test_unknown_speaker_on_utterance():
    t = _part1_base(
        utterances=[
            _utt("e1", "a", "Hello."),
            _utt("e2", "ghost", "Who am I?"),
        ]
    )
    report = validate_transcript(t)
    assert report.valid is False
    assert any(i.code == "unknown_speaker_id" for i in report.issues)


def test_duplicate_event_id():
    t = _part1_base(
        utterances=[
            _utt("e1", "a", "First."),
            _utt("e1", "b", "Duplicate id."),
        ]
    )
    report = validate_transcript(t)
    assert report.valid is False
    assert any(i.code == "duplicate_event_id" for i in report.issues)


def test_content_speaker_without_utterances():
    t = _part1_base(
        utterances=[_utt("e1", "a", "Only A speaks.")],
    )
    report = validate_transcript(t)
    assert report.valid is False
    assert any(i.code == "content_speaker_without_utterances" for i in report.issues)


def test_answer_span_optional_empty_ok():
    t = _part1_base(answer_bearing_spans=[])
    assert validate_transcript(t).valid is True


def test_answer_span_valid_offsets():
    text = "My name is Ada."
    # "Ada" at 11:14
    t = _part1_base(
        utterances=[
            _utt("e1", "a", text),
            _utt("e2", "b", "Thanks."),
        ],
        answer_bearing_spans=[
            AnswerBearingSpan(
                span_id="s1",
                event_id="e1",
                start_char=11,
                end_char=14,
                label="name",
            )
        ],
    )
    report = validate_transcript(t)
    assert report.valid is True
    assert report.answer_bearing_span_count == 1
    assert text[11:14] == "Ada"


def test_answer_span_out_of_bounds():
    t = _part1_base(
        answer_bearing_spans=[
            AnswerBearingSpan(
                span_id="s1",
                event_id="e1",
                start_char=0,
                end_char=999,
            )
        ]
    )
    report = validate_transcript(t)
    assert report.valid is False
    assert any(i.code == "answer_span_out_of_bounds" for i in report.issues)


def test_answer_span_unknown_event():
    t = _part1_base(
        answer_bearing_spans=[
            AnswerBearingSpan(
                span_id="s1",
                event_id="missing",
                start_char=0,
                end_char=1,
            )
        ]
    )
    report = validate_transcript(t)
    assert report.valid is False
    assert any(i.code == "answer_span_unknown_event" for i in report.issues)


def test_narrator_not_counted_as_content():
    t = InputTranscript(
        transcript_id="with-narr",
        part=PartNumber.PART_1,
        delivery_profile=DeliveryProfile.CONTENT_ONLY,
        speakers=[
            Speaker(speaker_id="n", role=SpeakerRole.NARRATOR),
            Speaker(speaker_id="a", role=SpeakerRole.CONTENT),
            Speaker(speaker_id="b", role=SpeakerRole.CONTENT),
        ],
        utterances=[
            _utt("e0", "n", "You will hear a conversation."),
            _utt("e1", "a", "Hello."),
            _utt("e2", "b", "Hi."),
        ],
    )
    report = validate_transcript(t)
    # content count still 2 → valid on speaker rules; warning for narrator in content_only
    assert report.speaker_map is not None
    assert report.speaker_map.content_speaker_count == 2
    assert report.speaker_map.narrator_voice_count == 1
    assert report.speaker_map.audio_voice_count == 3
    assert any(i.code == "narrator_in_content_only" for i in report.issues)
    assert report.valid is True  # warning only


def test_schema_rejects_empty_display_text():
    with pytest.raises(ValidationError):
        Utterance(event_id="e", speaker_id="a", display_text="   ")


def test_example_part1_valid_file():
    path = EXAMPLES / "part1_valid.json"
    transcript, report, schema_issues = load_and_validate_path(str(path))
    assert schema_issues == []
    assert transcript is not None
    assert report is not None
    assert report.valid is True
    assert report.speaker_map is not None
    assert report.speaker_map.content_speaker_count == 2
    assert report.answer_bearing_span_count == 2


def test_example_part1_invalid_speaker_count_file():
    path = EXAMPLES / "part1_invalid_speaker_count.json"
    _t, report, schema_issues = load_and_validate_path(str(path))
    assert schema_issues == []
    assert report is not None
    assert report.valid is False
    assert any(i.code == "invalid_content_speaker_count" for i in report.issues)


def test_example_part2_valid_file():
    path = EXAMPLES / "part2_valid.json"
    _t, report, schema_issues = load_and_validate_path(str(path))
    assert schema_issues == []
    assert report is not None
    assert report.valid is True
    assert report.answer_bearing_span_count == 0


def test_display_text_roundtrip_preserved():
    """Validator must not mutate display_text (load path identity)."""
    path = EXAMPLES / "part1_valid.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    transcript, report, _ = load_and_validate_path(str(path))
    assert report is not None and report.valid
    assert transcript is not None
    for src, utt in zip(raw["utterances"], transcript.utterances, strict=True):
        assert utt.display_text == src["display_text"]
