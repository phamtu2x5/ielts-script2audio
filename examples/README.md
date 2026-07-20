# Examples

Synthetic fixtures for Stage 1 validation. **Not** official IELTS materials.

| File | Purpose |
|------|---------|
| `part1_valid.json` | Part 1, 2 content speakers, optional answer spans |
| `part1_invalid_speaker_count.json` | Part 1 with only 1 content speaker (must fail) |
| `part2_valid.json` | Part 2 monologue, no answer spans |
| `part3_valid.json` | Part 3, 3 content speakers |
| `part4_valid.json` | Part 4 monologue |

```bash
ielts-s2a validate examples/part1_valid.json --pretty
ielts-s2a prepare examples/part3_valid.json --pretty
```
