"""Shared text patterns for normalisation and risk detection.

Keep patterns here so Stage 2.x rules evolve in one place without drift.
"""

from __future__ import annotations

import re

# Letter spelling: T-H-O-M-P-S-O-N or T.H.O.M.P.S.O.N
SPELLING_RE = re.compile(
    r"\b(?:[A-Za-z](?:-[A-Za-z]){2,}|(?:[A-Za-z]\.){2,}[A-Za-z]\.?)\b"
)

# UK-ish postcode (simplified) e.g. SW1A 1AA, EC1A 1BB
POSTCODE_RE = re.compile(
    r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b",
    re.IGNORECASE,
)

# Currency £12.50 or $20
CURRENCY_RE = re.compile(r"(£|\$|€)\s*(\d+(?:[.,]\d+)?)")

# Time 9:30 / 09:30 / 9.30 am
TIME_RE = re.compile(
    r"\b(\d{1,2})[:.](\d{2})\s*(am|pm|a\.m\.|p\.m\.)?\b",
    re.IGNORECASE,
)

# Phone-like digit groups (digit-by-digit policy; no double/triple)
PHONE_RE = re.compile(r"\b(?:\+?\d[\d\s\-()]{7,}\d)\b")

# Multi-word proper names (Capitalised tokens)
PROPER_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")

# ALL-CAPS acronyms (risk detector may filter further)
ACRONYM_RE = re.compile(r"\b([A-Z]{2,6})\b")

# Standalone integers / grouped thousands
NUMBER_RE = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d+)\b")

# Conventional abbreviations (normaliser table is separate)
ABBREV_KEYS = ("Mr.", "Mrs.", "Ms.", "Dr.", "St.", "No.", "etc.")
