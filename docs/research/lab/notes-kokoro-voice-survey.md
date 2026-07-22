# Lab notes: Kokoro voice survey (human)

**Date:** 2026-07-22  
**Provenance:** `[USER-PROVIDED]` listening feedback  
**Scope:** Kokoro only; Stage-2 spoken lines (spelling/postcode/phone/fee survey)  
**Not:** final TTS vendor selection; not production release

## Voices judged temporarily OK

| Voice ID | Gender (id prefix) | Notes |
|----------|--------------------|--------|
| `bf_alice` | f | OK |
| `bf_emma` | f | OK |
| `bf_lily` | f | OK |
| `bm_daniel` | m | OK |
| `bm_george` | m | OK |
| `bm_lewis` | m | OK |

**Count:** 3 female + 3 male British = **6** fixed IDs — enough for Part 1 (2) and Part 3 (up to 4) without a custom voice bank.

## Not listed as OK in this pass

From `gb_core` (8 British), not named in the OK list:

- `bf_isabella`
- `bm_fable`

Treat as **hold / lower priority** until re-listened.

## Casting implications (lab only)

- Prefer pairs/mixes **only from the 6 OK voices**.
- Part 1 default map updated toward OK set (e.g. emma + george, or lily + lewis).
- Part 3 can use 3–4 from the six with distinct timbre (mix F/M).
- Expressiveness still generally flat (earlier lab note); OK here means **usable**, not “expressive”.

## Open follow-ups

- [ ] Re-check codes (spelling/postcode/phone) **per OK voice** if not already done per-voice
- [ ] Pick stable Part 1 A/B pair for longer dialogue runs
- [ ] Part 3 3-speaker cast from the six
- [ ] Still `not_selected` as final backend — only Kokoro casting shortlist
