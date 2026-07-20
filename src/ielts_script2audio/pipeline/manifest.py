"""Build TTS-neutral synthesis manifest and requests."""

from __future__ import annotations

from ielts_script2audio.models.input_transcript import DeliveryProfile, InputTranscript
from ielts_script2audio.models.prepared import (
    PreparedUtterance,
    PronunciationRisk,
    ProtectedRegion,
    Segment,
    StepStatuses,
    SynthesisManifest,
    SynthesisRequest,
)
from ielts_script2audio.models.validation import (
    PipelineStepStatus,
    SpeakerMap,
    ValidationReport,
)


def build_requests(
    segments: list[Segment],
    *,
    locale: str,
) -> list[SynthesisRequest]:
    requests: list[SynthesisRequest] = []
    for seg in segments:
        requests.append(
            SynthesisRequest(
                request_id=f"req_{seg.segment_id}",
                segment_id=seg.segment_id,
                speaker_id=seg.speaker_id,
                voice_profile_id=seg.voice_profile_id,
                display_text=seg.display_text,
                spoken_text=seg.spoken_text,
                locale=locale,
                accent_target=None,
                pronunciation_overrides=list(seg.pronunciation_overrides),
                prosody=seg.prosody,
                protected_region_ids=list(seg.protected_region_ids),
                output_format="wav",
                sample_rate=None,
                status=PipelineStepStatus.READY,
            )
        )
    return requests


def build_manifest(
    transcript: InputTranscript,
    validation: ValidationReport,
    speaker_map: SpeakerMap,
    prepared: list[PreparedUtterance],
    risks: list[PronunciationRisk],
    protected_regions: list[ProtectedRegion],
    segments: list[Segment],
    requests: list[SynthesisRequest],
    open_questions: list[str],
) -> SynthesisManifest:
    blocking: list[str] = []
    if not validation.valid:
        blocking.append("validation failed — fix transcript before render")

    for risk in risks:
        if risk.answer_bearing and risk.requires_human_review:
            blocking.append(
                f"answer-bearing pronunciation risk needs review: {risk.risk_id} "
                f"({risk.token!r}, confidence={risk.confidence.value})"
            )

    for utt in prepared:
        if utt.requires_human_approval:
            blocking.append(
                f"normalisation requires human approval: event {utt.event_id}"
            )

    # Completeness invariants
    if len(prepared) != len(transcript.utterances):
        blocking.append("prepared utterance count != input utterance count")
    if len(segments) != len(prepared):
        blocking.append("segment count != prepared utterance count")
    if len(requests) != len(segments):
        blocking.append("request count != segment count")

    for src, prep in zip(transcript.utterances, prepared, strict=False):
        if prep.display_text != src.display_text:
            blocking.append(f"display_text mutated for event {src.event_id}")
            break

    step = StepStatuses(
        validation=PipelineStepStatus.EXECUTED,
        normalisation=PipelineStepStatus.EXECUTED,
        pronunciation_risk=PipelineStepStatus.EXECUTED,
        segmentation=PipelineStepStatus.EXECUTED,
        manifest=PipelineStepStatus.EXECUTED,
        render=PipelineStepStatus.NOT_EXECUTED,
    )

    return SynthesisManifest(
        manifest_id=f"mf_{transcript.transcript_id}",
        transcript_id=transcript.transcript_id,
        part=transcript.part,
        locale=transcript.locale,
        delivery_profile=transcript.delivery_profile
        if isinstance(transcript.delivery_profile, DeliveryProfile)
        else DeliveryProfile(transcript.delivery_profile),
        validation=validation,
        speaker_map=speaker_map,
        prepared_utterances=prepared,
        pronunciation_risks=risks,
        protected_regions=protected_regions,
        segments=segments,
        requests=requests,
        step_status=step,
        open_questions=open_questions,
        blocking_issues=blocking,
        metadata={
            "pipeline": "stage2",
            "tts_backend": "not_selected",
            "provider_neutral": True,
        },
    )
