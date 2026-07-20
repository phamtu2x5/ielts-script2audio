# Lab checklist: TTS ↔ Stage 1–2 compatibility

**Goal:** Verify a TTS backend can consume **exactly** what Stage 1–2 produce — not “model sounds nice on random text”.

**Does not authorize:** final TTS selection, silent script edits, production release.

## A. Input under test

| Artifact | How to produce |
|----------|----------------|
| Validated transcript | `examples/part1_valid.json` (or part3) |
| Manifest | `ielts-s2a prepare examples/part1_valid.json -o outputs/part1_manifest.json` |
| Voice map | `configs/voice_maps/kokoro_en_gb_part1.json` |

## B. Contract checks (automatic / by script)

- [ ] Manifest parses as JSON  
- [ ] `requests[]` non-empty; count == `segments[]` == prepared utterances  
- [ ] Each request has: `spoken_text`, `display_text`, `voice_profile_id`, `speaker_id`, `segment_id`  
- [ ] `spoken_text` ≠ raw display for normalised rows (e.g. spelling `T H O M P S O N`, postcode spoken form)  
- [ ] `display_text` unchanged vs input transcript (no silent script edit)  
- [ ] Voice map resolves every `voice_profile_id` used  
- [ ] Renderer writes one wav per request (or honest FAILED status)  
- [ ] Report file records EXECUTED/FAILED per segment  

Script: `scripts/lab_render_kokoro_from_manifest.py`

## C. Listening checks (human — Stage 1–2 relevant)

Listen with transcript **optional first**, then with manifest open.

### C1. Pipeline wiring
- [ ] Audio order matches segment order in manifest  
- [ ] Speaker A segments share one voice; speaker B another  
- [ ] Switching speakers is audible (Part 1)

### C2. Stage-2 normalisation value
- [ ] Spelling sequence (e004) is letter-wise intelligible  
- [ ] Postcode (e006) is usable (not read as a weird word)  
- [ ] Optional ablation: `--use-display-text` — if display is clearly worse, Stage-2 spoken_text is helping  

### C3. Answer-bearing
- [ ] Name / postcode regions not obviously clipped or swallowed  
- [ ] No need to “fix” script text to make TTS work (if broken → report, don’t silent-edit)

### C4. Failures to log (do not hide)
- [ ] Crash on long text / special chars  
- [ ] Empty audio  
- [ ] Wrong voice map  
- [ ] espeak/kokoro install issues on Colab  

## D. Pass / borderline / fail (lab verdict only)

| Verdict | Meaning |
|---------|---------|
| **Pass (lab)** | Manifest consumed; multi-speaker OK; codes mostly clear; ready to consider pilot adapter |
| **Borderline** | Works but codes or confusability weak — keep notes, maybe try Orpheus later |
| **Fail (lab)** | Cannot consume manifest / voices collapse / systematic code failure — do not Stage-4 |

This is **not** `final_selected`.

## E. After lab

1. Fill `docs/research/lab/notes-kokoro-part1.md` (template below in README).  
2. Keep wavs out of git if large (gitignored `*.wav`).  
3. Decide next: Orpheus comparison **or** pilot adapter design.  
