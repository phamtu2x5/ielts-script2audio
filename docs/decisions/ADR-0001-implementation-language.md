# ADR-0001: Implementation language

- **Status:** Accepted
- **Date:** 2026-07-20
- **Deciders:** Project owner (Phạm Văn Tư), Claude (control-plane design session)

## Context

Repo greenfield: chưa có production code, package manifest, hay schema runtime. Cần chọn ngôn ngữ cho:

- domain models và validators (transcript, speaker, segment, manifest);
- CLI / library entrypoints;
- (sau) adapter TTS, tooling audio, benchmark harness.

Yêu cầu kiến trúc: provider-neutral core, JSON contracts rõ, dễ viết test, phù hợp research/audio stack về sau — nhưng **không** chọn TTS backend trong ADR này.

## Options considered

1. **Python 3.11+**  
   Pydantic/jsonschema, ecosystem audio/ML/research mạnh, scriptability cao cho Mode C/D sau này.

2. **TypeScript / Node**  
   JSON-first, DX tốt cho CLI/web; ecosystem TTS local và forced-alignment thường mỏng hơn Python.

3. **Để TBD**  
   Trì hoãn; chặn Stage 1 schema/code.

4. **Dual package (schema JSON + multi-lang bindings)**  
   Linh hoạt lâu dài nhưng overhead cao cho MVP; không phù hợp greenfield tối giản.

## Decision

Chọn **Python 3.11+** làm implementation language duy nhất cho MVP và các stage gần (schema, validators, normaliser, segmenter, manifest builder, sau này adapter).

Provenance: `[USER-PROVIDED]` (phê duyệt trong session thiết kế 2026-07-20).

## Consequences

### Tích cực

- Khớp `.gitignore` hiện có (`.venv/`, `__pycache__`, models).
- Thuận tiện formal hóa contract bằng Pydantic v2 / JSON Schema.
- Dễ tích hợp research TTS open-weight và tool đo audio sau này (khi tới Stage 3–5).

### Tiêu cực / trade-off

- Nếu sau này cần UI web nặng, có thể bổ sung TypeScript chỉ ở lớp presentation (P2) — **không** nhân đôi domain core.
- Cần `pyproject.toml`, tooling lint/test Python ở Stage 1 (chưa có trong Stage 0).

### Follow-up

- Stage 1: tạo package layout Python tối thiểu + validators.
- Không thêm ngôn ngữ thứ hai cho domain logic trừ khi có ADR superseding.

## References

- [`docs/architecture-principles.md`](../architecture-principles.md)
- [`docs/roadmap.md`](../roadmap.md) — Stage 1
- [`docs/prompts/system-control.md`](../prompts/system-control.md) — P0 TTS-neutral schema
