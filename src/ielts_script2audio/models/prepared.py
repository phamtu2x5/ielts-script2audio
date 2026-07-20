"""Stage 2 contracts: normalised utterances, risks, segments, synthesis manifest.

Provider-neutral — no vendor TTS fields (ADR-0002).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ielts_script2audio.models.input_transcript import DeliveryProfile, PartNumber
from ielts_script2audio.models.validation import (
    PipelineStepStatus,
    SpeakerMap,
    ValidationReport,
)


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NormalisationChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    """e.g. spelling_sequence, postcode, currency, abbreviation, number"""

    original: str
    replacement: str
    reason: str


class PronunciationOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    spoken_form: str
    hint: str | None = None
    engine_override: str | None = None
    """Provider-agnostic hint only; adapters may map later."""


class PreparedUtterance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    speaker_id: str
    display_text: str
    spoken_text: str
    normalisation_changes: list[NormalisationChange] = Field(default_factory=list)
    pronunciation_overrides: list[PronunciationOverride] = Field(default_factory=list)
    prosody: dict[str, Any] | None = None
    protected_region_ids: list[str] = Field(default_factory=list)
    requires_human_approval: bool = False


class PronunciationRisk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_id: str
    event_id: str
    token: str
    category: str
    original_form: str
    spoken_form: str | None = None
    pronunciation_hint: str | None = None
    ipa_or_phoneme_hint: str | None = None
    engine_override: str | None = None
    confidence: Confidence
    answer_bearing: bool = False
    requires_human_review: bool = False


class ProtectedRegion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region_id: str
    event_id: str
    start_char: int
    end_char: int
    label: str | None = None
    source: str = "answer_bearing_span"
    """Provenance of protection (answer span, manual, …)."""


class Segment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_id: str
    event_id: str
    event_type: str = "content_utterance"
    speaker_id: str
    voice_profile_id: str
    display_text: str
    spoken_text: str
    pronunciation_overrides: list[PronunciationOverride] = Field(default_factory=list)
    prosody: dict[str, Any] | None = None
    protected_region_ids: list[str] = Field(default_factory=list)
    estimated_duration_ms: int | None = None
    actual_duration_ms: int | None = None
    output_filename: str | None = None
    render_status: PipelineStepStatus = PipelineStepStatus.PLANNED
    qa_status: PipelineStepStatus = PipelineStepStatus.PLANNED


class SynthesisRequest(BaseModel):
    """TTS-neutral request (system-control §18)."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    segment_id: str
    speaker_id: str
    voice_profile_id: str
    display_text: str
    spoken_text: str
    locale: str | None = "en-GB"
    accent_target: str | None = None
    pronunciation_overrides: list[PronunciationOverride] = Field(default_factory=list)
    prosody: dict[str, Any] | None = None
    protected_region_ids: list[str] = Field(default_factory=list)
    output_format: str = "wav"
    sample_rate: int | None = None
    status: PipelineStepStatus = PipelineStepStatus.READY


class StepStatuses(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validation: PipelineStepStatus
    normalisation: PipelineStepStatus
    pronunciation_risk: PipelineStepStatus
    segmentation: PipelineStepStatus
    manifest: PipelineStepStatus
    render: PipelineStepStatus = PipelineStepStatus.NOT_EXECUTED
    """Render is out of Stage 2 scope."""


class SynthesisManifest(BaseModel):
    """Provider-neutral synthesis package — Stage 2 output."""

    model_config = ConfigDict(extra="forbid")

    manifest_id: str
    transcript_id: str
    part: PartNumber
    locale: str
    delivery_profile: DeliveryProfile
    schema_version: str = "stage2.v1"
    validation: ValidationReport
    speaker_map: SpeakerMap
    prepared_utterances: list[PreparedUtterance]
    pronunciation_risks: list[PronunciationRisk] = Field(default_factory=list)
    protected_regions: list[ProtectedRegion] = Field(default_factory=list)
    segments: list[Segment] = Field(default_factory=list)
    requests: list[SynthesisRequest] = Field(default_factory=list)
    step_status: StepStatuses
    open_questions: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    """Human-readable blockers before any future release/render."""

    metadata: dict[str, Any] = Field(default_factory=dict)
