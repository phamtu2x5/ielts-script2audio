# IELTS Script-to-Audio

## Project purpose

Build a provider-neutral system that converts completed IELTS-style Listening transcripts into TTS-ready data, rendered audio segments, and validated final audio.

Claude is the control plane and system architect.

Claude is not the TTS engine. TTS models are replaceable execution backends that may be open-weight, API-based, self-hosted, or hybrid.

## Current state

- The repository is newly initialized.
- No production implementation exists yet.
- Completed transcripts will be provided as input.
- Transcript generation, question generation, answer generation, and band prediction are out of scope.
- The TTS backend has not been selected.
- Default working mode is System Design.

## Target flow

```text
Completed transcript
→ validation
→ spoken-form normalisation
→ pronunciation-risk detection
→ phrase-safe segmentation
→ provider-neutral synthesis manifest
→ replaceable TTS adapter
→ audio QA
→ assembly and human review
```

## Non-negotiable rules

- Preserve transcript facts, logic, speaker intent, and answer-bearing phrases.
- Preserve `display_text` exactly.
- Use `spoken_text` only for safe TTS normalisation.
- Do not invent narrator wording, durations, timestamps, benchmark results, or official IELTS rules.
- Do not select a TTS provider before defining requirements and a benchmark.
- Do not claim TTS, ASR, alignment, audio inspection, or human review was executed unless it actually ran.
- Unknown values must be `[OPEN-QUESTION]`, `null`, or `TBD`.
- Keep core domain logic independent of any TTS provider.
- Significant architectural decisions require an ADR in `docs/decisions/`.
- Do not silently expand project scope.

## IELTS speaker constraints

- Part 1: exactly 2 content speakers.
- Part 2: exactly 1 content speaker.
- Part 3: 2–4 content speakers.
- Part 4: exactly 1 content speaker.
- Narrator voices are not content speakers.
- One speaker must keep one voice identity throughout a Part.

## Working process

For significant tasks:

1. Inspect the repository.
2. State assumptions and open questions.
3. Propose a bounded plan.
4. Wait for approval before major implementation.
5. Make the smallest coherent change.
6. Add or update tests.
7. Run relevant checks.
8. Report exactly what was executed.
9. Report what remains planned or unavailable.

## Detailed operating specification

The full control specification is stored at:

`docs/prompts/system-control.md`

Read that file before working on:

- system architecture;
- transcript preparation;
- TTS backend research;
- render orchestration;
- pronunciation or prosody rules;
- segmentation and timeline design;
- audio QA and release logic.

Do not load or reproduce the entire specification when it is irrelevant to the current task.

## Project documentation

Maintain:

- `README.md`
- `docs/product-goal.md`
- `docs/architecture-principles.md`
- `docs/ielts-audio-rules.md`
- `docs/roadmap.md`
- `docs/decisions/`
