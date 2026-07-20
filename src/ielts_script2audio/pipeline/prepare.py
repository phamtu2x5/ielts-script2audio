"""Orchestrate Stage 2: validate → normalise → risk → segment → manifest.

Policy (Stage 2.1):
- Always produce a manifest when the input *schema* is valid, even if domain
  validation fails — so producers can inspect blocking_issues.
- CLI `prepare` exits non-zero when validation.valid is false (unless
  --allow-invalid). Fail-soft data, fail-hard process by default.
"""

from __future__ import annotations

from ielts_script2audio.models.input_transcript import InputTranscript
from ielts_script2audio.models.prepared import ProtectedRegion, SynthesisManifest
from ielts_script2audio.models.validation import ValidationIssue
from ielts_script2audio.pipeline.manifest import build_manifest, build_requests
from ielts_script2audio.pipeline.normalise import normalise_utterance
from ielts_script2audio.pipeline.risks import detect_pronunciation_risks
from ielts_script2audio.pipeline.segment import assign_voice_profile_ids, segment_utterances
from ielts_script2audio.validation.transcript import validate_transcript


def prepare_transcript(transcript: InputTranscript) -> SynthesisManifest:
    """Run full Stage 2 preparation. Does not call TTS or write audio."""

    validation = validate_transcript(transcript)
    assert validation.speaker_map is not None
    speaker_map = validation.speaker_map

    voice_profiles = assign_voice_profile_ids(speaker_map)
    updated_entries = [
        entry.model_copy(
            update={"voice_profile_id": voice_profiles.get(entry.speaker_id)}
        )
        for entry in speaker_map.entries
    ]
    speaker_map = speaker_map.model_copy(update={"entries": updated_entries})

    protected_regions: list[ProtectedRegion] = []
    spans_by_event: dict[str, list[str]] = {}
    for span in transcript.answer_bearing_spans:
        protected_regions.append(
            ProtectedRegion(
                region_id=span.span_id,
                event_id=span.event_id,
                start_char=span.start_char,
                end_char=span.end_char,
                label=span.label,
                source="answer_bearing_span",
            )
        )
        spans_by_event.setdefault(span.event_id, []).append(span.span_id)

    prepared = [
        normalise_utterance(
            utt,
            locale=transcript.locale,
            protected_region_ids=spans_by_event.get(utt.event_id, []),
        )
        for utt in transcript.utterances
    ]

    risks = detect_pronunciation_risks(prepared, transcript.answer_bearing_spans)
    segments = segment_utterances(prepared, voice_profiles)
    requests = build_requests(segments, locale=transcript.locale)

    open_questions = list(validation.open_questions)
    if any(r.category == "phone_or_code" for r in risks):
        open_questions.append(
            "OQ-08: phone/code reading uses digit-by-digit; "
            "double/triple convention not defined"
        )

    return build_manifest(
        transcript=transcript,
        validation=validation,
        speaker_map=speaker_map,
        prepared=prepared,
        risks=risks,
        protected_regions=protected_regions,
        segments=segments,
        requests=requests,
        open_questions=open_questions,
    )


def prepare_path(
    path: str,
) -> tuple[SynthesisManifest | None, list[ValidationIssue]]:
    """Load JSON transcript path and prepare manifest."""
    from ielts_script2audio.validation.transcript import load_and_validate_path

    transcript, _report, schema_issues = load_and_validate_path(path)
    if schema_issues or transcript is None:
        return None, schema_issues
    return prepare_transcript(transcript), []
