"""Input transcript contracts (Stage 1).

Formalises OQ-02 for MVP: fields required to validate speakers and completeness
before spoken-form normalisation. TTS-provider fields are intentionally absent.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PartNumber(int, Enum):
    """IELTS Listening part index."""

    PART_1 = 1
    PART_2 = 2
    PART_3 = 3
    PART_4 = 4


class SpeakerRole(str, Enum):
    CONTENT = "content"
    NARRATOR = "narrator"


class DeliveryProfile(str, Enum):
    """MVP default is content_only (ADR session 2026-07-20)."""

    CONTENT_ONLY = "content_only"
    FULL_EXAM = "full_exam"


class Speaker(BaseModel):
    model_config = ConfigDict(extra="forbid")

    speaker_id: str = Field(..., min_length=1)
    role: SpeakerRole
    label: str | None = None
    """Human-facing label from source transcript, if any."""


class Utterance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(..., min_length=1)
    speaker_id: str = Field(..., min_length=1)
    display_text: str
    """Original transcript text — must be preserved exactly downstream."""

    @field_validator("display_text")
    @classmethod
    def display_text_must_be_non_empty_after_strip_check(cls, value: str) -> str:
        # Keep exact text (including intentional leading/trailing space) but reject blank-only.
        if value.strip() == "":
            raise ValueError("display_text must not be empty or whitespace-only")
        return value


class AnswerBearingSpan(BaseModel):
    """Optional answer protection metadata.

    Character offsets refer to display_text of the referenced utterance (0-based,
    end-exclusive). Offsets are validated when present.
    """

    model_config = ConfigDict(extra="forbid")

    span_id: str = Field(..., min_length=1)
    event_id: str = Field(..., min_length=1)
    start_char: int = Field(..., ge=0)
    end_char: int = Field(..., ge=0)
    label: str | None = None

    @field_validator("end_char")
    @classmethod
    def end_after_start(cls, end_char: int, info: Any) -> int:
        start = info.data.get("start_char")
        if start is not None and end_char <= start:
            raise ValueError("end_char must be greater than start_char")
        return end_char


class InputTranscript(BaseModel):
    """Structured completed transcript — Stage 1 input boundary."""

    model_config = ConfigDict(extra="forbid")

    transcript_id: str = Field(..., min_length=1)
    part: PartNumber
    locale: str = Field(default="en-GB", min_length=2)
    """Default en-GB [USER-PROVIDED]; override per transcript allowed."""

    delivery_profile: DeliveryProfile = DeliveryProfile.CONTENT_ONLY
    speakers: list[Speaker] = Field(..., min_length=1)
    utterances: list[Utterance] = Field(..., min_length=1)
    answer_bearing_spans: list[AnswerBearingSpan] = Field(default_factory=list)
    """Optional. Empty list means no answer protection metadata provided."""

    metadata: dict[str, Any] = Field(default_factory=dict)
    """Opaque producer metadata; not interpreted by Stage 1 validators."""
