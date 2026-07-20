"""Validation report and speaker map contracts."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ielts_script2audio.models.input_transcript import PartNumber, SpeakerRole


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class PipelineStepStatus(str, Enum):
    """Truthful pipeline step status (system-control §5)."""

    PLANNED = "PLANNED"
    READY = "READY"
    EXECUTED = "EXECUTED"
    NOT_EXECUTED = "NOT_EXECUTED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: IssueSeverity
    message: str
    path: str | None = None
    """JSON-ish path hint, e.g. utterances[2].speaker_id"""

    event_id: str | None = None
    speaker_id: str | None = None
    requires_human_approval: bool = False


class SpeakerMapEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    speaker_id: str
    role: SpeakerRole
    label: str | None = None
    utterance_count: int = Field(..., ge=0)
    voice_profile_id: str | None = None
    """Abstract casting id — assigned in later stages, not a backend voice id."""


class SpeakerMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part: PartNumber
    content_speaker_count: int
    narrator_voice_count: int
    audio_voice_count: int
    entries: list[SpeakerMapEntry]


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript_id: str
    part: PartNumber
    valid: bool
    """True only when there are zero ERROR-severity issues."""

    issues: list[ValidationIssue] = Field(default_factory=list)
    speaker_map: SpeakerMap | None = None
    utterance_count: int = 0
    answer_bearing_span_count: int = 0
    step_status: PipelineStepStatus = PipelineStepStatus.EXECUTED
    """Status of the validation step itself (this report was produced)."""

    open_questions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)
