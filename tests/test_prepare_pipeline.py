"""Stage 2 pipeline tests: normalise, risk, segment, manifest."""

from __future__ import annotations

import json
from pathlib import Path

from ielts_script2audio.models.input_transcript import (
    AnswerBearingSpan,
    InputTranscript,
    PartNumber,
    Speaker,
    SpeakerRole,
    Utterance,
)
from ielts_script2audio.pipeline.normalise import normalise_utterance
from ielts_script2audio.pipeline.prepare import prepare_path, prepare_transcript
from ielts_script2audio.models.validation import PipelineStepStatus

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def _utt(eid: str, sid: str, text: str) -> Utterance:
    return Utterance(event_id=eid, speaker_id=sid, display_text=text)


def _part1(*utterances: Utterance, spans: list[AnswerBearingSpan] | None = None) -> InputTranscript:
    return InputTranscript(
        transcript_id="prep-test",
        part=PartNumber.PART_1,
        speakers=[
            Speaker(speaker_id="a", role=SpeakerRole.CONTENT),
            Speaker(speaker_id="b", role=SpeakerRole.CONTENT),
        ],
        utterances=list(utterances),
        answer_bearing_spans=spans or [],
    )


def test_normalise_preserves_display_text():
    u = _utt("e1", "a", "It's Sarah Thompson. That's T-H-O-M-P-S-O-N.")
    p = normalise_utterance(u)
    assert p.display_text == u.display_text
    # Stronger pacing + end-anchor so last letter is less often swallowed
    assert "T... H... O... M... P... S... O... N... N" in p.spoken_text
    assert "T-H-O-M-P-S-O-N" not in p.spoken_text
    assert any(c.kind == "spelling_sequence" for c in p.normalisation_changes)


def test_normalise_postcode():
    u = _utt("e1", "a", "SW1A 1AA.")
    p = normalise_utterance(u)
    assert p.display_text == "SW1A 1AA."
    assert any(c.kind == "postcode" for c in p.normalisation_changes)
    # Digits spoken as words; ellipsis paces items; last A reinforced
    assert "one" in p.spoken_text.lower()
    assert "A... A" in p.spoken_text
    assert p.spoken_text.count("A") >= 3  # ... A ... A ... A (end anchor)


def test_normalise_phone_end_anchor():
    u = _utt("e1", "a", "Call 020 7946 0958.")
    p = normalise_utterance(u)
    assert p.display_text == u.display_text
    assert "eight" in p.spoken_text.lower()
    # last digit reinforced
    assert p.spoken_text.lower().count("eight") >= 2


def test_normalise_currency_and_time():
    u = _utt("e1", "a", "It costs £12.50 at 9:30 am.")
    p = normalise_utterance(u)
    kinds = {c.kind for c in p.normalisation_changes}
    assert "currency" in kinds
    assert "time" in kinds
    assert "pound" in p.spoken_text.lower()


def test_prepare_part1_example_manifest():
    manifest, issues = prepare_path(str(EXAMPLES / "part1_valid.json"))
    assert issues == []
    assert manifest is not None
    assert manifest.validation.valid is True
    assert manifest.schema_version == "stage2.v1"
    # Expanded Part 1 lab fixture
    assert len(manifest.prepared_utterances) == 15
    assert len(manifest.prepared_utterances) == len(manifest.segments)
    assert len(manifest.requests) == len(manifest.segments)
    assert len(manifest.protected_regions) == 4
    assert manifest.step_status.render == PipelineStepStatus.NOT_EXECUTED
    assert manifest.step_status.manifest == PipelineStepStatus.EXECUTED
    assert manifest.metadata.get("provider_neutral") is True
    assert manifest.metadata.get("tts_backend") == "not_selected"

    # display_text identity
    raw = json.loads((EXAMPLES / "part1_valid.json").read_text(encoding="utf-8"))
    for src, prep in zip(raw["utterances"], manifest.prepared_utterances, strict=True):
        assert prep.display_text == src["display_text"]

    # protected regions from answer spans
    assert len(manifest.protected_regions) == 4
    assert {r.region_id for r in manifest.protected_regions} == {
        "ans_name",
        "ans_postcode",
        "ans_phone",
        "ans_fee",
    }

    # voice profiles abstract
    for entry in manifest.speaker_map.entries:
        assert entry.voice_profile_id == f"vp_{entry.speaker_id}"

    # requests neutral shape
    req = manifest.requests[0]
    assert req.output_format == "wav"
    assert req.status == PipelineStepStatus.READY
    assert "backend" not in req.model_dump()


def test_prepare_completeness_no_drop_merge():
    t = _part1(
        _utt("e1", "a", "Hello."),
        _utt("e2", "b", "Hi."),
        _utt("e3", "a", "How are you?"),
    )
    m = prepare_transcript(t)
    assert [u.event_id for u in m.prepared_utterances] == ["e1", "e2", "e3"]
    assert [s.event_id for s in m.segments] == ["e1", "e2", "e3"]
    assert len(m.requests) == 3


def test_answer_bearing_risk_flagged():
    text = "It's Sarah Thompson here."
    # "Sarah Thompson" roughly
    start = text.index("Sarah")
    end = start + len("Sarah Thompson")
    t = _part1(
        _utt("e1", "a", text),
        _utt("e2", "b", "Thanks."),
        spans=[
            AnswerBearingSpan(
                span_id="n1",
                event_id="e1",
                start_char=start,
                end_char=end,
                label="name",
            )
        ],
    )
    m = prepare_transcript(t)
    name_risks = [
        r
        for r in m.pronunciation_risks
        if r.answer_bearing and r.category == "proper_name"
    ]
    assert name_risks
    assert any(r.requires_human_review for r in name_risks)
    assert any("answer-bearing" in b for b in m.blocking_issues)


def test_phone_digit_by_digit_no_double_triple():
    u = _utt("e1", "a", "Call me on 020 7946 0958.")
    p = normalise_utterance(u)
    assert "double" not in p.spoken_text.lower()
    assert "triple" not in p.spoken_text.lower()
    assert any(c.kind == "phone_or_digit_string" for c in p.normalisation_changes)


def test_prepare_part3_and_part4_examples():
    for name, content_n in (("part3_valid.json", 3), ("part4_valid.json", 1)):
        manifest, issues = prepare_path(str(EXAMPLES / name))
        assert issues == []
        assert manifest is not None
        assert manifest.validation.valid is True
        assert manifest.speaker_map is not None
        assert manifest.speaker_map.content_speaker_count == content_n
        assert len(manifest.requests) == len(manifest.segments) == len(
            manifest.prepared_utterances
        )


def test_postcode_does_not_emit_nested_acronym_risks():
    """Acronym detector should not flag fragments inside a postcode."""
    t = _part1(
        _utt("e1", "a", "My postcode is SW1A 1AA."),
        _utt("e2", "b", "Thanks."),
    )
    m = prepare_transcript(t)
    acronyms = [r for r in m.pronunciation_risks if r.category == "acronym"]
    # SW / AA etc. inside postcode should be suppressed
    assert not any(r.token in {"SW", "AA", "SW1A"} for r in acronyms)
    assert any(r.category == "postcode" for r in m.pronunciation_risks)


def test_prepare_policy_soft_manifest_hard_cli_semantics():
    """Domain-invalid input still yields a manifest with blocking_issues."""
    t = InputTranscript(
        transcript_id="bad",
        part=PartNumber.PART_1,
        speakers=[Speaker(speaker_id="a", role=SpeakerRole.CONTENT)],
        utterances=[_utt("e1", "a", "Only one content speaker.")],
    )
    m = prepare_transcript(t)
    assert m.validation.valid is False
    assert m.requests  # still built for inspection
    assert any("validation failed" in b for b in m.blocking_issues)
