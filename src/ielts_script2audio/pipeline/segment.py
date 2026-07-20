"""Phrase-safe segmentation (Stage 2).

MVP policy: one segment per prepared utterance (preserves completeness and
avoids illegal splits inside names/codes/answer spans). Future stages may
sub-segment only at safe clause boundaries outside protected regions.
"""

from __future__ import annotations

from ielts_script2audio.models.prepared import PreparedUtterance, Segment
from ielts_script2audio.models.validation import PipelineStepStatus, SpeakerMap


def assign_voice_profile_ids(speaker_map: SpeakerMap) -> dict[str, str]:
    """Abstract voice_profile_id per speaker (not backend voice ids)."""
    mapping: dict[str, str] = {}
    for entry in speaker_map.entries:
        mapping[entry.speaker_id] = f"vp_{entry.speaker_id}"
    return mapping


def segment_utterances(
    prepared: list[PreparedUtterance],
    voice_profiles: dict[str, str],
) -> list[Segment]:
    segments: list[Segment] = []
    for index, utt in enumerate(prepared, start=1):
        vp = voice_profiles.get(utt.speaker_id, f"vp_{utt.speaker_id}")
        segments.append(
            Segment(
                segment_id=f"seg_{index:04d}",
                event_id=utt.event_id,
                event_type="content_utterance",
                speaker_id=utt.speaker_id,
                voice_profile_id=vp,
                display_text=utt.display_text,
                spoken_text=utt.spoken_text,
                pronunciation_overrides=list(utt.pronunciation_overrides),
                prosody=utt.prosody,
                protected_region_ids=list(utt.protected_region_ids),
                estimated_duration_ms=None,
                actual_duration_ms=None,
                output_filename=None,
                render_status=PipelineStepStatus.PLANNED,
                qa_status=PipelineStepStatus.PLANNED,
            )
        )
    return segments
