# Roadmap

Trạng thái: **Stage 3 desk research xong — shortlist pending lab; backend `not_selected`.**  
TTS backend: **chưa chọn**. Render/audio: **chưa có** (`benchmark: NOT_EXECUTED`).

## Nguyên tắc roadmap

- Làm **đủ dùng theo stage**, hoàn thiện dần; không chặn tiến độ để “đầy đủ tuyệt đối” theo toàn bộ system-control.
- Thay đổi spec/rules sau này là bình thường — giữ contract ổn định, mở rộng incremental.
- Làm P0 trước P1; P2 chỉ khi được yêu cầu.
- Không chọn TTS backend trước Stage 3 (requirements + criteria + benchmark design + evidence).
- Mỗi stage có “done” rõ; không đánh `EXECUTED` cho tool chưa chạy.
- ADR cho quyết định kiến trúc lớn.

## Stage 0 — Documentation & decisions ✅ (đợt này)

**Mục tiêu:** neo product intent, architecture, rules, ADR.

| Deliverable | Trạng thái |
|-------------|------------|
| `README.md` | Điền trong đợt này |
| `docs/product-goal.md` | Điền trong đợt này |
| `docs/architecture-principles.md` | Điền trong đợt này |
| `docs/ielts-audio-rules.md` | Điền trong đợt này |
| `docs/roadmap.md` | Điền trong đợt này |
| ADR-0001 language (Python 3.11+) | Accepted |
| ADR-0002 TTS adapter boundary | Accepted |
| `docs/prompts/system-control.md` | Đã có sẵn |

**Done khi:** docs non-empty, không mâu thuẫn control spec; ADR có Decision rõ; không production code lọt.

## Stage 1 — Input schema & validators ✅ (implemented)

**Mục tiêu:** formal hóa input/output contracts bằng Python; chưa TTS.

| Deliverable | Vị trí |
|-------------|--------|
| Package Python 3.11+ | `pyproject.toml`, `src/ielts_script2audio/` |
| Pydantic models | `models/input_transcript.py`, `models/validation.py` |
| Validator | `validation/transcript.py` → `validate_transcript` |
| CLI | `ielts-s2a validate <path>` |
| Fixtures | `examples/part1_valid.json`, `part1_invalid_speaker_count.json`, `part2_valid.json` |
| Tests | `tests/test_validate_transcript.py`, `tests/test_cli.py` |

**OQ-02 (field bắt buộc):** đã chốt tối thiểu cho Stage 1:

- Bắt buộc: `transcript_id`, `part`, `speakers[]` (`speaker_id`, `role`), `utterances[]` (`event_id`, `speaker_id`, `display_text`)
- Mặc định: `locale=en-GB`, `delivery_profile=content_only`, `answer_bearing_spans=[]`
- Optional: `label` speaker, span `label`, `metadata`

**Done khi:** transcript hợp lệ/không hợp lệ được reject/pass có test; chưa cần normaliser đầy đủ.

Schema chi tiết: [`docs/schemas/input-transcript-stage1.md`](schemas/input-transcript-stage1.md)

**Chạy kiểm tra:**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
ielts-s2a validate examples/part1_valid.json --pretty
```

**Execution status:** `pytest` + CLI validate/prepare đã **EXECUTED** (green) trong dev session.

## Stage 2 — MVP pipeline → synthesis manifest ✅

**Mục tiêu:** end-to-end **không render**.

```text
validate → normalise (en-GB default) → pronunciation risk → segment → manifest
```

| Deliverable | Vị trí |
|-------------|--------|
| Models | `models/prepared.py` — PreparedUtterance, Risk, Segment, SynthesisRequest/Manifest |
| Normaliser | `pipeline/normalise.py` |
| Risk detector | `pipeline/risks.py` |
| Segmenter | `pipeline/segment.py` (MVP: 1 utterance = 1 segment, phrase-safe by not splitting) |
| Manifest builder | `pipeline/manifest.py`, orchestrator `pipeline/prepare.py` |
| CLI | `ielts-s2a prepare <path> [-o out.json]` |
| Tests | `tests/test_prepare_pipeline.py`, `tests/test_cli_prepare.py` |

**Done khi:** fixture Part 1 sinh manifest parse được, đủ request/segment, `render: NOT_EXECUTED` — **đã xác nhận 34 passed + CLI smoke.**

Defaults: content-only; answer optional; locale en-GB.

```bash
ielts-s2a prepare examples/part1_valid.json --pretty -o outputs/part1_manifest.json
```

### Stage 2.1 — harden MVP (không “full polish”) ✅

| Việc | Ghi chú |
|------|---------|
| Shared `pipeline/patterns.py` | Tránh drift regex normalise/risk |
| Fixtures Part 3 + Part 4 | `examples/part3_valid.json`, `part4_valid.json` |
| Giảm acronym false positive | Skip range postcode/phone/spelling + allowlist nhỏ |
| Policy prepare | Schema OK → luôn có manifest; domain invalid → `blocking_issues` + CLI exit 1 (trừ `--allow-invalid`) |
| Docs status | Reflect tests EXECUTED |

**Cố ý để sau (incremental):** dates, measurements, %, booking codes, sub-segmentation, sparse prosody, full casting.

## Stage 3 — Mode C: TTS research & benchmark design ✅ (desk)

**Mục tiêu:** shortlist có evidence; **không** bắt buộc chốt vendor.

| Deliverable | File |
|-------------|------|
| Requirements | [`docs/research/tts-requirements.md`](research/tts-requirements.md) |
| Evaluation criteria | [`docs/research/tts-evaluation-criteria.md`](research/tts-evaluation-criteria.md) |
| Candidates (desk) | [`docs/research/tts-candidates.md`](research/tts-candidates.md) |
| Benchmark plan | [`docs/research/tts-benchmark-plan.md`](research/tts-benchmark-plan.md) |
| Shortlist + status | [`docs/research/tts-shortlist.md`](research/tts-shortlist.md) |

**Constraints (user):** Colab L4/A100 + git/notebook; open-weight prior; API research-only (budget); model 0.3B–0.5B+ được xét; SSML không quyết prior hiện tại.

**Shortlist lab (rev.2):** CosyVoice 2/3 (0.5B), F5-TTS (nếu license OK), Kokoro baseline; API hold research-only.  
**Hold:** Coqui XTTS (license/maintenance).

**Done (desk) khi:** requirements + criteria + candidates + benchmark plan + shortlist ≠ final — **đã có** (đã cập nhật constraints).

**Lab assets (sẵn sàng chạy):** notebook + script Kokoro đọc manifest Stage 2 — xem `docs/research/lab/`.  
**Chưa xong (lab execution):** render/nghe trên Colab — `NOT_EXECUTED` cho đến khi bạn chạy GPU.

OQ-06/07: **đã chốt tạm** trong `docs/research/deployment-constraints.md`.

## Stage 4 — First adapter & Mode D render orchestration

**Mục tiêu:** một adapter thật + fake adapter cho contract test.

- Implement adapter boundary (ADR-0002)
- Voice inventory mapping (`voice_profile_id` → `backend_voice_id`)
- Per-segment render, logging, retry
- Selective re-render
- Vẫn không claim QA đã pass nếu chưa có tool

**Done khi:** render được segment từ manifest; lỗi segment được ghi nhận; domain core vẫn không import vendor ngoài adapter package.

## Stage 5 — Validation plane & release

**Mục tiêu:** release có evidence.

- Forced alignment (khi tool có)
- ASR back-check (không phải bằng chứng duy nhất)
- Loudness / clipping / silence checks
- Assembly timeline (duration provenance)
- Human review checklist (đặc biệt answer-bearing)
- Release report + release-blocking rules

**Done khi:** có quy trình release; blocking conditions được enforce; status trung thực.

## Ngoài roadmap (P2 — không làm trừ khi được yêu cầu)

- UI
- Scoring / band prediction
- Question / distractor generation
- Psychometric analysis

## Open questions theo dõi

| ID | Câu hỏi | Stage liên quan |
|----|---------|-----------------|
| OQ-02 | Input schema fields bắt buộc chi tiết | 1 |
| OQ-06 | Deployment preference | 3 |
| OQ-07 | Privacy / budget / hardware | 3 |
| OQ-08 | Convention đọc phone/code (digit vs double/triple) | 2 |
| OQ-09 | Multi-Part full test batch? (đề xuất: single Part trước) | 2–4 |
| OQ-10 | Human approval workflow | 2, 5 |

## Bước tiếp theo khuyến nghị

Sau Stage 0: **bắt đầu Stage 1** — định nghĩa schema `InputTranscript` + speaker validator + 1–2 fixtures (không chọn TTS, không render).
