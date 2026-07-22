"""Spoken-form normalisation (display_text → spoken_text).

Rules are conservative en-GB defaults [USER-PROVIDED locale].
Does not mutate display_text. Ambiguous expansions request human approval.

Incremental: extend patterns/rules over time; do not aim for full coverage upfront.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ielts_script2audio.models.input_transcript import AnswerBearingSpan, Utterance
from ielts_script2audio.models.prepared import (
    NormalisationChange,
    PreparedUtterance,
    PronunciationOverride,
)
from ielts_script2audio.pipeline.patterns import (
    ABBREV_KEYS,
    CURRENCY_RE,
    NUMBER_RE,
    PHONE_RE,
    POSTCODE_RE,
    SPELLING_RE,
    TIME_RE,
)

_ABBREV: dict[str, str] = {
    "Mr.": "Mister",
    "Mrs.": "Missus",
    "Ms.": "Miz",
    "Dr.": "Doctor",
    "St.": "Street",  # may be Saint — flagged for human approval
    "No.": "number",
    "etc.": "etcetera",
}

_ABBREV_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(ABBREV_KEYS, key=len, reverse=True)) + r")\b"
)

_ONES = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]
_TENS = [
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
]


def _int_to_en(n: int) -> str:
    if n < 0:
        return "minus " + _int_to_en(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return _TENS[t] if o == 0 else f"{_TENS[t]}-{_ONES[o]}"
    if n < 1000:
        h, r = divmod(n, 100)
        return _ONES[h] + " hundred" if r == 0 else f"{_ONES[h]} hundred and {_int_to_en(r)}"
    if n < 1_000_000:
        th, r = divmod(n, 1000)
        head = _int_to_en(th) + " thousand"
        return head if r == 0 else f"{head} {_int_to_en(r)}"
    return " ".join(_ONES[int(ch)] if ch.isdigit() else ch for ch in str(n))


def _paced_join(parts: list[str], *, mode: str = "codes") -> str:
    """Join tokens with pause cues so plain TTS reads more slowly.

    Used for spelling / postcode / phone-style sequences. Does not change
    display_text; only spoken pacing for engines without SSML.

    Does **not** repeat the final token (that sounds like a content error).
    Trailing audio silence for cut-off issues belongs in the lab renderer.

    mode:
      - codes: stronger pauses (letters/digits that must stay intelligible)
      - light: milder pauses
    """
    cleaned = [p for p in parts if p]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if mode == "codes":
        # "T... H... O... N" — pause between items, no doubled last token
        return "... ".join(cleaned)
    return ", ".join(cleaned)


def _spell_out_letters(token: str) -> str:
    letters = re.findall(r"[A-Za-z]", token)
    return _paced_join([ch.upper() for ch in letters], mode="codes")


def _speak_postcode(token: str) -> str:
    """Speak postcode with outward/inward grouping when spacing is present.

    Example: SW1A 1AA → "S... W... one... A... one... A... A"
    (space in original becomes a longer spoken boundary via '; ')
    """
    chunks = re.split(r"\s+", token.strip())
    spoken_chunks: list[str] = []
    for chunk in chunks:
        compact = re.sub(r"\s+", "", chunk.upper())
        parts: list[str] = []
        for ch in compact:
            if ch.isalpha():
                parts.append(ch)
            elif ch.isdigit():
                parts.append(_ONES[int(ch)])
        if parts:
            spoken_chunks.append(_paced_join(parts, mode="codes"))
    if not spoken_chunks:
        return token
    if len(spoken_chunks) == 1:
        return spoken_chunks[0]
    # Stronger boundary between postcode halves — ellipsis only (no ';' —
    # some TTS engines vocalise semicolon as a word or odd glottal).
    return "... ... ".join(spoken_chunks)


def _speak_currency(symbol: str, amount: str) -> str:
    amount_norm = amount.replace(",", "")
    if "." in amount_norm:
        whole_s, frac_s = amount_norm.split(".", 1)
    elif "," in amount and amount.count(",") == 1 and len(amount.split(",")[1]) <= 2:
        whole_s, frac_s = amount.split(",", 1)
    else:
        whole_s, frac_s = amount_norm, ""

    try:
        whole = int(whole_s)
    except ValueError:
        return f"{symbol}{amount}"

    major = {
        "£": ("pound", "pounds"),
        "$": ("dollar", "dollars"),
        "€": ("euro", "euros"),
    }.get(symbol, ("unit", "units"))
    unit = major[0] if whole == 1 else major[1]
    spoken = f"{_int_to_en(whole)} {unit}"
    if frac_s:
        frac_s = (frac_s + "00")[:2]
        try:
            frac = int(frac_s)
        except ValueError:
            return spoken
        if frac:
            minor = {
                "£": "pence",
                "$": "cents",
                "€": "cents",
            }.get(symbol, "point " + " ".join(_ONES[int(c)] for c in frac_s))
            spoken += f" and {_int_to_en(frac)} {minor}"
    return spoken


def _speak_time(h: str, m: str, ampm: str | None) -> str:
    hour = int(h)
    minute = int(m)
    hour_s = _int_to_en(hour)
    if minute == 0:
        body = f"{hour_s} o'clock"
    elif minute < 10:
        body = f"{hour_s} oh {_int_to_en(minute)}"
    else:
        body = f"{hour_s} {_int_to_en(minute)}"
    if ampm:
        ap = ampm.lower().replace(".", "")
        body += " A M" if ap.startswith("a") else " P M"
    return body


def _speak_phone(token: str) -> str:
    """Speak phone using original spacing as group boundaries (no double/triple).

    Example: 020 7946 0958
      → "zero... two... zero... ; ... seven... nine... four... six... ; ... zero... nine... five... eight"
    """
    # Prefer digit groups as written; fall back to flat digits
    groups = re.findall(r"\d+", token)
    if not groups:
        return token
    spoken_groups: list[str] = []
    for group in groups:
        spoken_groups.append(
            _paced_join([_ONES[int(d)] for d in group], mode="codes")
        )
    if len(spoken_groups) == 1:
        return spoken_groups[0]
    # Group boundary with ellipsis only (no ';' — avoid odd spoken "semicolon")
    return "... ... ".join(spoken_groups)


def _speak_number_token(token: str) -> str:
    raw = token.replace(",", "")
    if not raw.isdigit():
        return token
    if len(raw) >= 5:
        return " ".join(_ONES[int(d)] for d in raw)
    return _int_to_en(int(raw))


@dataclass
class _NormState:
    text: str
    changes: list[NormalisationChange]
    overrides: list[PronunciationOverride]
    needs_approval: bool = False


def _replace_all(
    state: _NormState,
    pattern: re.Pattern[str],
    replacer,
    kind: str,
    reason: str,
    as_override: bool = False,
) -> None:
    def _sub(match: re.Match[str]) -> str:
        original = match.group(0)
        replacement = replacer(match)
        if replacement == original:
            return original
        state.changes.append(
            NormalisationChange(
                kind=kind,
                original=original,
                replacement=replacement,
                reason=reason,
            )
        )
        if as_override:
            state.overrides.append(
                PronunciationOverride(
                    token=original,
                    spoken_form=replacement,
                    hint=reason,
                )
            )
        return replacement

    state.text = pattern.sub(_sub, state.text)


def normalise_utterance(
    utterance: Utterance,
    *,
    locale: str = "en-GB",
    protected_region_ids: list[str] | None = None,
) -> PreparedUtterance:
    """Produce spoken_text from display_text without mutating display_text."""

    _ = locale  # reserved for future locale packs; en-GB rules applied for now
    state = _NormState(text=utterance.display_text, changes=[], overrides=[])

    _replace_all(
        state,
        SPELLING_RE,
        lambda m: _spell_out_letters(m.group(0)),
        kind="spelling_sequence",
        reason="Expand letter-by-letter spelling for TTS",
        as_override=True,
    )

    _replace_all(
        state,
        POSTCODE_RE,
        lambda m: _speak_postcode(m.group(1)),
        kind="postcode",
        reason="Read UK-style postcode as letters and digits",
        as_override=True,
    )

    _replace_all(
        state,
        CURRENCY_RE,
        lambda m: _speak_currency(m.group(1), m.group(2)),
        kind="currency",
        reason="Expand currency amount to spoken en-GB form",
    )

    _replace_all(
        state,
        TIME_RE,
        lambda m: _speak_time(m.group(1), m.group(2), m.group(3)),
        kind="time",
        reason="Expand clock time for TTS",
    )

    _replace_all(
        state,
        PHONE_RE,
        lambda m: _speak_phone(m.group(0)),
        kind="phone_or_digit_string",
        reason="Read phone-like digit strings digit-by-digit (no double/triple convention)",
        as_override=True,
    )

    def _abbrev_repl(m: re.Match[str]) -> str:
        key = m.group(1)
        if key == "St.":
            state.needs_approval = True
            state.changes.append(
                NormalisationChange(
                    kind="abbreviation_ambiguous",
                    original=key,
                    replacement=_ABBREV[key],
                    reason="St. may mean Street or Saint — default Street needs human check",
                )
            )
            return _ABBREV[key]
        return _ABBREV.get(key, key)

    def _abbrev_sub(match: re.Match[str]) -> str:
        original = match.group(0)
        replacement = _abbrev_repl(match)
        if replacement != original and not any(
            c.original == original and c.kind.startswith("abbreviation")
            for c in state.changes
        ):
            state.changes.append(
                NormalisationChange(
                    kind="abbreviation",
                    original=original,
                    replacement=replacement,
                    reason="Expand conventional title/abbreviation",
                )
            )
        return replacement

    state.text = _ABBREV_RE.sub(_abbrev_sub, state.text)

    def _num_sub(match: re.Match[str]) -> str:
        original = match.group(0)
        replacement = _speak_number_token(original)
        if replacement == original:
            return original
        state.changes.append(
            NormalisationChange(
                kind="number",
                original=original,
                replacement=replacement,
                reason="Expand number to spoken words (long strings digit-by-digit)",
            )
        )
        return replacement

    state.text = NUMBER_RE.sub(_num_sub, state.text)

    return PreparedUtterance(
        event_id=utterance.event_id,
        speaker_id=utterance.speaker_id,
        display_text=utterance.display_text,
        spoken_text=state.text,
        normalisation_changes=state.changes,
        pronunciation_overrides=state.overrides,
        prosody=None,
        protected_region_ids=list(protected_region_ids or []),
        requires_human_approval=state.needs_approval,
    )


def build_protected_regions(
    spans: list[AnswerBearingSpan],
) -> list[tuple[str, AnswerBearingSpan]]:
    """Map answer spans to region ids (region_id == span_id for traceability)."""
    return [(span.span_id, span) for span in spans]
