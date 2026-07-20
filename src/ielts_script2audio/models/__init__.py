"""Domain models and validation reports for Stage 1."""

from ielts_script2audio.models.input_transcript import (
    AnswerBearingSpan,
    DeliveryProfile,
    InputTranscript,
    PartNumber,
    Speaker,
    SpeakerRole,
    Utterance,
)
from ielts_script2audio.models.prepared import (
    PreparedUtterance,
    PronunciationRisk,
    ProtectedRegion,
    Segment,
    SynthesisManifest,
    SynthesisRequest,
)
from ielts_script2audio.models.validation import (
    IssueSeverity,
    PipelineStepStatus,
    SpeakerMap,
    SpeakerMapEntry,
    ValidationIssue,
    ValidationReport,
)

__all__ = [
    "AnswerBearingSpan",
    "DeliveryProfile",
    "InputTranscript",
    "IssueSeverity",
    "PartNumber",
    "PipelineStepStatus",
    "PreparedUtterance",
    "PronunciationRisk",
    "ProtectedRegion",
    "Segment",
    "Speaker",
    "SpeakerMap",
    "SpeakerMapEntry",
    "SpeakerRole",
    "SynthesisManifest",
    "SynthesisRequest",
    "Utterance",
    "ValidationIssue",
    "ValidationReport",
]
