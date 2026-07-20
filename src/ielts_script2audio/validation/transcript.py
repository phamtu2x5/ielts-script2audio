"""Validate structured InputTranscript against IELTS-style hard constraints.

Stage 1 scope:
- speaker / part counts
- speaker id consistency
- utterance completeness (ids, order preserved as given, non-empty text via schema)
- optional answer-bearing span referential integrity and offsets

Does not: normalise spoken form, segment, call TTS, invent content.
"""

from __future__ import annotations

from collections import Counter

from ielts_script2audio.models.input_transcript import (
    DeliveryProfile,
    InputTranscript,
    PartNumber,
    SpeakerRole,
)
from ielts_script2audio.models.validation import (
    IssueSeverity,
    PipelineStepStatus,
    SpeakerMap,
    SpeakerMapEntry,
    ValidationIssue,
    ValidationReport,
)

# Content speaker hard constraints [DESIGN-PROPOSAL / system-control §6]
_CONTENT_SPEAKER_RULES: dict[PartNumber, range | int] = {
    PartNumber.PART_1: 2,
    PartNumber.PART_2: 1,
    PartNumber.PART_3: range(2, 5),  # 2..4 inclusive
    PartNumber.PART_4: 1,
}


def _content_count_ok(part: PartNumber, count: int) -> bool:
    rule = _CONTENT_SPEAKER_RULES[part]
    if isinstance(rule, range):
        return count in rule
    return count == rule


def _expected_content_description(part: PartNumber) -> str:
    rule = _CONTENT_SPEAKER_RULES[part]
    if isinstance(rule, range):
        return f"{rule.start}–{rule.stop - 1}"
    return str(rule)


def validate_transcript(transcript: InputTranscript) -> ValidationReport:
    """Run Stage 1 validation and build SpeakerMap."""

    issues: list[ValidationIssue] = []
    open_questions: list[str] = []

    speaker_ids = [s.speaker_id for s in transcript.speakers]
    speaker_id_set = set(speaker_ids)

    # --- duplicate speaker definitions ---
    dup_speakers = [sid for sid, n in Counter(speaker_ids).items() if n > 1]
    for sid in dup_speakers:
        issues.append(
            ValidationIssue(
                code="duplicate_speaker_id",
                severity=IssueSeverity.ERROR,
                message=f"speaker_id appears more than once in speakers list: {sid!r}",
                path="speakers",
                speaker_id=sid,
            )
        )

    content_speakers = [s for s in transcript.speakers if s.role == SpeakerRole.CONTENT]
    narrator_speakers = [s for s in transcript.speakers if s.role == SpeakerRole.NARRATOR]
    content_count = len({s.speaker_id for s in content_speakers})
    narrator_count = len({s.speaker_id for s in narrator_speakers})

    # --- part content speaker counts ---
    if not _content_count_ok(transcript.part, content_count):
        issues.append(
            ValidationIssue(
                code="invalid_content_speaker_count",
                severity=IssueSeverity.ERROR,
                message=(
                    f"Part {transcript.part.value} requires "
                    f"{_expected_content_description(transcript.part)} content speaker(s); "
                    f"found {content_count}"
                ),
                path="speakers",
            )
        )

    # --- delivery profile vs narrator ---
    if (
        transcript.delivery_profile == DeliveryProfile.CONTENT_ONLY
        and narrator_count > 0
    ):
        issues.append(
            ValidationIssue(
                code="narrator_in_content_only",
                severity=IssueSeverity.WARNING,
                message=(
                    "delivery_profile is content_only but narrator speakers are defined; "
                    "narrator events are unexpected for MVP default"
                ),
                path="speakers",
            )
        )

    if (
        transcript.delivery_profile == DeliveryProfile.FULL_EXAM
        and narrator_count == 0
    ):
        open_questions.append(
            "delivery_profile is full_exam but no narrator speaker is defined "
            "[OPEN-QUESTION]: provide narrator script/speakers or switch to content_only"
        )
        issues.append(
            ValidationIssue(
                code="missing_narrator_for_full_exam",
                severity=IssueSeverity.WARNING,
                message=(
                    "full_exam delivery without narrator speaker — "
                    "do not invent narrator wording"
                ),
                path="speakers",
                requires_human_approval=True,
            )
        )

    # --- utterance speaker references & completeness ---
    seen_event_ids: set[str] = set()
    utterance_counts: Counter[str] = Counter()

    if not transcript.utterances:
        issues.append(
            ValidationIssue(
                code="no_utterances",
                severity=IssueSeverity.ERROR,
                message="transcript has no utterances",
                path="utterances",
            )
        )

    for index, utt in enumerate(transcript.utterances):
        path = f"utterances[{index}]"

        if utt.event_id in seen_event_ids:
            issues.append(
                ValidationIssue(
                    code="duplicate_event_id",
                    severity=IssueSeverity.ERROR,
                    message=f"duplicate event_id: {utt.event_id!r}",
                    path=f"{path}.event_id",
                    event_id=utt.event_id,
                )
            )
        else:
            seen_event_ids.add(utt.event_id)

        if utt.speaker_id not in speaker_id_set:
            issues.append(
                ValidationIssue(
                    code="unknown_speaker_id",
                    severity=IssueSeverity.ERROR,
                    message=(
                        f"utterance references unknown speaker_id: {utt.speaker_id!r}"
                    ),
                    path=f"{path}.speaker_id",
                    event_id=utt.event_id,
                    speaker_id=utt.speaker_id,
                )
            )
        else:
            utterance_counts[utt.speaker_id] += 1

    # Content speakers with zero utterances
    for s in content_speakers:
        if utterance_counts.get(s.speaker_id, 0) == 0 and s.speaker_id not in dup_speakers:
            issues.append(
                ValidationIssue(
                    code="content_speaker_without_utterances",
                    severity=IssueSeverity.ERROR,
                    message=(
                        f"content speaker {s.speaker_id!r} has no utterances "
                        "(still counted toward part speaker rules)"
                    ),
                    path="speakers",
                    speaker_id=s.speaker_id,
                )
            )

    # Speakers defined but never used (narrator may be intentional for later)
    for s in transcript.speakers:
        if utterance_counts.get(s.speaker_id, 0) == 0 and s.role == SpeakerRole.NARRATOR:
            issues.append(
                ValidationIssue(
                    code="unused_narrator_speaker",
                    severity=IssueSeverity.WARNING,
                    message=f"narrator speaker {s.speaker_id!r} has no utterances",
                    path="speakers",
                    speaker_id=s.speaker_id,
                )
            )

    # --- answer-bearing spans (optional) ---
    utterances_by_event = {u.event_id: u for u in transcript.utterances}
    seen_span_ids: set[str] = set()

    for index, span in enumerate(transcript.answer_bearing_spans):
        path = f"answer_bearing_spans[{index}]"

        if span.span_id in seen_span_ids:
            issues.append(
                ValidationIssue(
                    code="duplicate_span_id",
                    severity=IssueSeverity.ERROR,
                    message=f"duplicate span_id: {span.span_id!r}",
                    path=f"{path}.span_id",
                    event_id=span.event_id,
                )
            )
        else:
            seen_span_ids.add(span.span_id)

        utt = utterances_by_event.get(span.event_id)
        if utt is None:
            issues.append(
                ValidationIssue(
                    code="answer_span_unknown_event",
                    severity=IssueSeverity.ERROR,
                    message=(
                        f"answer-bearing span references unknown event_id: {span.event_id!r}"
                    ),
                    path=f"{path}.event_id",
                    event_id=span.event_id,
                )
            )
            continue

        text_len = len(utt.display_text)
        if span.start_char >= text_len or span.end_char > text_len:
            issues.append(
                ValidationIssue(
                    code="answer_span_out_of_bounds",
                    severity=IssueSeverity.ERROR,
                    message=(
                        f"span {span.span_id!r} offsets [{span.start_char}, {span.end_char}) "
                        f"out of bounds for display_text length {text_len}"
                    ),
                    path=path,
                    event_id=span.event_id,
                )
            )
        elif utt.display_text[span.start_char : span.end_char].strip() == "":
            issues.append(
                ValidationIssue(
                    code="answer_span_empty_slice",
                    severity=IssueSeverity.ERROR,
                    message=f"span {span.span_id!r} selects empty/whitespace text",
                    path=path,
                    event_id=span.event_id,
                )
            )

    # --- build speaker map (even if invalid — useful for diagnostics) ---
    entries: list[SpeakerMapEntry] = []
    # Preserve speakers list order; unique by first occurrence
    seen_for_map: set[str] = set()
    for s in transcript.speakers:
        if s.speaker_id in seen_for_map:
            continue
        seen_for_map.add(s.speaker_id)
        entries.append(
            SpeakerMapEntry(
                speaker_id=s.speaker_id,
                role=s.role,
                label=s.label,
                utterance_count=utterance_counts.get(s.speaker_id, 0),
                voice_profile_id=None,
            )
        )

    # Recount unique roles for map (after de-dupe)
    unique_content = sum(1 for e in entries if e.role == SpeakerRole.CONTENT)
    unique_narrator = sum(1 for e in entries if e.role == SpeakerRole.NARRATOR)

    speaker_map = SpeakerMap(
        part=transcript.part,
        content_speaker_count=unique_content,
        narrator_voice_count=unique_narrator,
        audio_voice_count=unique_content + unique_narrator,
        entries=entries,
    )

    error_count = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)

    return ValidationReport(
        transcript_id=transcript.transcript_id,
        part=transcript.part,
        valid=error_count == 0,
        issues=issues,
        speaker_map=speaker_map,
        utterance_count=len(transcript.utterances),
        answer_bearing_span_count=len(transcript.answer_bearing_spans),
        step_status=PipelineStepStatus.EXECUTED,
        open_questions=open_questions,
        metadata={
            "locale": transcript.locale,
            "delivery_profile": transcript.delivery_profile.value,
        },
    )


def load_and_validate_path(path: str) -> tuple[InputTranscript | None, ValidationReport | None, list[ValidationIssue]]:
    """Load JSON file and validate. Returns (transcript|None, report|None, schema_issues)."""
    import json
    from pathlib import Path

    from pydantic import ValidationError

    raw_path = Path(path)
    schema_issues: list[ValidationIssue] = []
    try:
        data = json.loads(raw_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        schema_issues.append(
            ValidationIssue(
                code="input_unreadable",
                severity=IssueSeverity.ERROR,
                message=f"cannot read JSON transcript: {exc}",
                path=str(raw_path),
            )
        )
        return None, None, schema_issues

    try:
        transcript = InputTranscript.model_validate(data)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", ()))
            schema_issues.append(
                ValidationIssue(
                    code="schema_validation_error",
                    severity=IssueSeverity.ERROR,
                    message=err.get("msg", "schema error"),
                    path=loc or None,
                )
            )
        return None, None, schema_issues

    report = validate_transcript(transcript)
    return transcript, report, []
