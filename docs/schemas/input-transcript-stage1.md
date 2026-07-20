# InputTranscript schema (Stage 1)

Formalises **OQ-02** for the validation boundary. Provider-neutral; no TTS fields.

## Required fields

| Field | Type | Notes |
|-------|------|--------|
| `transcript_id` | string | Stable id |
| `part` | `1 \| 2 \| 3 \| 4` | Listening part |
| `speakers` | array (min 1) | See Speaker |
| `utterances` | array (min 1) | See Utterance |

### Speaker

| Field | Type | Required |
|-------|------|----------|
| `speaker_id` | string | yes |
| `role` | `"content" \| "narrator"` | yes |
| `label` | string \| null | no |

### Utterance

| Field | Type | Required |
|-------|------|----------|
| `event_id` | string | yes (unique in file) |
| `speaker_id` | string | yes (must exist in `speakers`) |
| `display_text` | string | yes (not whitespace-only; preserved exactly) |

## Defaults

| Field | Default | Provenance |
|-------|---------|------------|
| `locale` | `"en-GB"` | `[USER-PROVIDED]` |
| `delivery_profile` | `"content_only"` | `[USER-PROVIDED]` |
| `answer_bearing_spans` | `[]` | optional |
| `metadata` | `{}` | opaque |

## Optional answer-bearing span

| Field | Type | Notes |
|-------|------|--------|
| `span_id` | string | unique |
| `event_id` | string | must reference an utterance |
| `start_char` | int ≥ 0 | 0-based, into `display_text` |
| `end_char` | int | exclusive; `> start_char`; ≤ len(display_text) |
| `label` | string \| null | optional |

## Validation codes (domain)

| Code | Severity | Meaning |
|------|----------|---------|
| `invalid_content_speaker_count` | error | Part speaker rule failed |
| `duplicate_speaker_id` | error | Repeated id in `speakers` |
| `duplicate_event_id` | error | Repeated utterance id |
| `unknown_speaker_id` | error | Utterance points to missing speaker |
| `content_speaker_without_utterances` | error | Content speaker never speaks |
| `answer_span_unknown_event` | error | Span event missing |
| `answer_span_out_of_bounds` | error | Offsets outside text |
| `answer_span_empty_slice` | error | Span is blank |
| `duplicate_span_id` | error | Repeated span id |
| `narrator_in_content_only` | warning | Narrator present under content_only |
| `missing_narrator_for_full_exam` | warning | full_exam without narrator |
| `unused_narrator_speaker` | warning | Narrator defined, no lines |
| `schema_validation_error` | error | Pydantic/JSON shape failure |
| `input_unreadable` | error | File/JSON parse failure |

## Content speaker rules

| Part | Content speakers |
|------|------------------|
| 1 | exactly 2 |
| 2 | exactly 1 |
| 3 | 2–4 |
| 4 | exactly 1 |

Narrator is not a content speaker.

## Implementation

- Models: `src/ielts_script2audio/models/`
- Validator: `validate_transcript()` in `src/ielts_script2audio/validation/transcript.py`
- CLI: `ielts-s2a validate <path>`
