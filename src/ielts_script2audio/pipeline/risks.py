"""Pronunciation risk detection (Stage 2).

Heuristic and incremental: prefer fewer false blockers over exhaustive coverage.
"""

from __future__ import annotations

from ielts_script2audio.models.input_transcript import AnswerBearingSpan
from ielts_script2audio.models.prepared import (
    Confidence,
    PreparedUtterance,
    PronunciationRisk,
)
from ielts_script2audio.pipeline.patterns import (
    ACRONYM_RE,
    PHONE_RE,
    POSTCODE_RE,
    PROPER_RE,
    SPELLING_RE,
)

# Common function/acronyms that rarely need TTS review as letter-spelled risks.
_ACRONYM_ALLOWLIST = frozenset(
    {
        "OK",
        "TV",
        "UK",
        "US",
        "USA",
        "EU",
        "AM",
        "PM",
        "ID",
        "PC",
        "AI",
        "IT",
        "PDF",
        "GPS",
        "FAQ",
    }
)


def _overlaps_answer(
    event_id: str,
    start: int,
    end: int,
    spans: list[AnswerBearingSpan],
) -> bool:
    for span in spans:
        if span.event_id != event_id:
            continue
        if start < span.end_char and end > span.start_char:
            return True
    return False


def _covered_ranges(text: str) -> list[tuple[int, int]]:
    """Ranges already claimed by spelling/postcode/phone — skip nested acronyms."""
    ranges: list[tuple[int, int]] = []
    for pattern in (SPELLING_RE, POSTCODE_RE, PHONE_RE):
        for m in pattern.finditer(text):
            ranges.append((m.start(), m.end()))
    return ranges


def _inside(ranges: list[tuple[int, int]], start: int, end: int) -> bool:
    for rs, re_ in ranges:
        if start >= rs and end <= re_:
            return True
        if start < re_ and end > rs:
            return True
    return False


def detect_pronunciation_risks(
    prepared: list[PreparedUtterance],
    answer_spans: list[AnswerBearingSpan],
) -> list[PronunciationRisk]:
    """Heuristic risks from display_text patterns + normalisation flags."""

    risks: list[PronunciationRisk] = []
    counter = 0

    def _add(
        *,
        event_id: str,
        token: str,
        category: str,
        original: str,
        spoken: str | None,
        confidence: Confidence,
        start: int,
        end: int,
        hint: str | None = None,
    ) -> None:
        nonlocal counter
        counter += 1
        answer = _overlaps_answer(event_id, start, end, answer_spans)
        needs_review = answer and confidence != Confidence.HIGH
        if confidence == Confidence.LOW:
            needs_review = True
        risks.append(
            PronunciationRisk(
                risk_id=f"risk_{counter:04d}",
                event_id=event_id,
                token=token,
                category=category,
                original_form=original,
                spoken_form=spoken,
                pronunciation_hint=hint,
                confidence=confidence,
                answer_bearing=answer,
                requires_human_review=needs_review,
            )
        )

    for utt in prepared:
        text = utt.display_text
        covered = _covered_ranges(text)

        def _spoken_for(original: str) -> str | None:
            return next(
                (c.replacement for c in utt.normalisation_changes if c.original == original),
                None,
            )

        for m in SPELLING_RE.finditer(text):
            _add(
                event_id=utt.event_id,
                token=m.group(0),
                category="spelling_sequence",
                original=m.group(0),
                spoken=_spoken_for(m.group(0)),
                confidence=Confidence.HIGH,
                start=m.start(),
                end=m.end(),
                hint="Letter-by-letter spelling",
            )

        for m in POSTCODE_RE.finditer(text):
            _add(
                event_id=utt.event_id,
                token=m.group(0),
                category="postcode",
                original=m.group(0),
                spoken=_spoken_for(m.group(0)),
                confidence=Confidence.HIGH,
                start=m.start(),
                end=m.end(),
                hint="UK-style postcode",
            )

        for m in PHONE_RE.finditer(text):
            _add(
                event_id=utt.event_id,
                token=m.group(0),
                category="phone_or_code",
                original=m.group(0),
                spoken=_spoken_for(m.group(0)),
                confidence=Confidence.MEDIUM,
                start=m.start(),
                end=m.end(),
                hint="Digit-by-digit; double/triple convention not applied [OPEN-QUESTION OQ-08]",
            )

        for m in PROPER_RE.finditer(text):
            if SPELLING_RE.fullmatch(m.group(0)):
                continue
            _add(
                event_id=utt.event_id,
                token=m.group(0),
                category="proper_name",
                original=m.group(0),
                spoken=None,
                confidence=Confidence.MEDIUM,
                start=m.start(),
                end=m.end(),
                hint="Multi-word proper name — verify TTS pronunciation",
            )

        for m in ACRONYM_RE.finditer(text):
            tok = m.group(1)
            if tok in _ACRONYM_ALLOWLIST:
                continue
            if _inside(covered, m.start(), m.end()):
                continue
            # Skip single-token fragments that are only letters inside a larger postcode-like form
            if any(ch.isdigit() for ch in text[max(0, m.start() - 1) : m.end() + 1]):
                # adjacent digit often means postcode/code fragment already handled
                if _inside(covered, max(0, m.start() - 2), min(len(text), m.end() + 2)):
                    continue
            _add(
                event_id=utt.event_id,
                token=tok,
                category="acronym",
                original=tok,
                spoken=None,
                confidence=Confidence.LOW,
                start=m.start(),
                end=m.end(),
                hint="Acronym may be letter-spelled or word-read",
            )

        for ch in utt.normalisation_changes:
            if ch.kind == "abbreviation_ambiguous":
                idx = text.find(ch.original)
                _add(
                    event_id=utt.event_id,
                    token=ch.original,
                    category="abbreviation_ambiguous",
                    original=ch.original,
                    spoken=ch.replacement,
                    confidence=Confidence.LOW,
                    start=max(idx, 0),
                    end=max(idx, 0) + len(ch.original),
                    hint=ch.reason,
                )

    return risks
