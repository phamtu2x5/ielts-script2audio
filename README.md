# IELTS Script-to-Audio

Hệ thống **provider-neutral** chuyển transcript IELTS-style Listening đã hoàn thiện thành dữ liệu TTS-ready, audio segment (giai đoạn sau), và audio đã kiểm chứng.

## Vai trò

| Thành phần | Vai trò |
|------------|---------|
| **Claude** | Control plane và kiến trúc sư hệ thống — quyết định, validation, normalisation, segmentation, QA orchestration |
| **TTS backend** | Execution plane có thể thay thế — open-weight, API, self-hosted, hoặc hybrid |
| **Adapter** | Ranh giới duy nhất dịch TTS-neutral contract → payload/provider cụ thể |

Claude **không phải** TTS engine. Backend cụ thể **chưa được chọn** và không được mặc định trước khi có requirements + benchmark.

## Phạm vi

**Trong phạm vi**

- Validation transcript và speaker
- Spoken-form normalisation (`spoken_text`)
- Phát hiện pronunciation risk
- Phrase-safe segmentation
- Provider-neutral synthesis manifest
- (Sau) TTS adapter, render, audio QA, assembly, human review

**Ngoài phạm vi**

- Sinh transcript, câu hỏi, đáp án, distractor
- Band prediction / scoring / psychometric
- Tuyên bố sản phẩm là đề IELTS chính thức
- Sao chép transcript/audio có bản quyền

## MVP 1 (hiện tại)

```text
structured transcript
→ kiểm tra transcript và speaker
→ spoken-form normalisation (locale mặc định: en-GB)
→ phát hiện pronunciation risk
→ phrase-safe segmentation
→ provider-neutral synthesis manifest
```

- Delivery profile mặc định: **content-only**
- Answer-bearing spans: **optional**
- Dừng **trước** adapter/render

## Pipeline mục tiêu (đầy đủ)

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

## Chế độ làm việc (với Claude)

| Mode | Khi nào |
|------|---------|
| **A — System Design** | Kiến trúc, schema, roadmap, trade-off (mặc định hiện tại) |
| **B — Transcript Preparation** | Có transcript cụ thể cần chuẩn bị TTS-ready |
| **C — TTS Research** | Nghiên cứu/so sánh backend; không chốt khi thiếu evidence |
| **D — Render Orchestration** | Backend + adapter + tool đã sẵn sàng |

Đặc tả vận hành đầy đủ: [`docs/prompts/system-control.md`](docs/prompts/system-control.md)

## Nguyên tắc cốt lõi

- Giữ nguyên dữ kiện, logic, speaker intent, answer-bearing phrases
- `display_text` = transcript gốc (bất biến); `spoken_text` = cách TTS đọc
- Không bịa narrator wording, duration, timestamp, benchmark, hay quy định IELTS “official” khi chưa xác minh
- Domain core độc lập provider; thay đổi kiến trúc lớn → ADR trong `docs/decisions/`
- Trạng thái pipeline trung thực: không đánh `EXECUTED` nếu chưa chạy thật

## Cấu trúc repo

```text
.
├── CLAUDE.md                 # Hướng dẫn agent / project charter
├── README.md                 # Tài liệu này
├── configs/                  # Cấu hình (sẽ bổ sung)
├── examples/                 # Fixture transcript/manifest (sẽ bổ sung)
├── outputs/                  # Output sinh ra (gitignored, giữ .gitkeep)
└── docs/
    ├── product-goal.md
    ├── architecture-principles.md
    ├── ielts-audio-rules.md
    ├── roadmap.md
    ├── decisions/            # ADR
    ├── prompts/system-control.md
    └── research/             # Ghi chú Mode C (sau)
```

## Trạng thái dự án

| Hạng mục | Trạng thái |
|----------|------------|
| Implementation language | Python 3.11+ — [ADR-0001](docs/decisions/ADR-0001-implementation-language.md) |
| TTS adapter boundary | [ADR-0002](docs/decisions/ADR-0002-tts-adapter-boundary.md) |
| Production code | Stage 2.1 — validate + prepare → TTS-neutral manifest (chưa render) |
| TTS backend | **Chưa chọn** — desk shortlist trong `docs/research/` |
| Stage hiện tại | Stage 3 desk research xong; lab benchmark `NOT_EXECUTED` |

## Tài liệu

- [Mục tiêu sản phẩm](docs/product-goal.md)
- [Nguyên tắc kiến trúc](docs/architecture-principles.md)
- [Quy tắc audio IELTS-style](docs/ielts-audio-rules.md)
- [Roadmap](docs/roadmap.md)
- [Quyết định kiến trúc (ADR)](docs/decisions/README.md)
- [System control prompt](docs/prompts/system-control.md)
- [TTS research (Mode C)](docs/research/README.md)

## Cài đặt & validate (Stage 1)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
ielts-s2a validate examples/part1_valid.json --pretty
ielts-s2a prepare examples/part1_valid.json --pretty -o outputs/part1_manifest.json
```

`validate` — kiểm tra transcript.  
`prepare` — validate + normalise + risk + segment + **synthesis manifest** trung lập.  
**Không** gọi TTS, **không** render audio.

## Làm việc với repo này

1. Đọc `CLAUDE.md` và `docs/prompts/system-control.md` trước khi thay đổi kiến trúc hoặc pipeline.
2. Thay đổi kiến trúc lớn → viết/cập nhật ADR.
3. Không chọn TTS backend ngoài Stage 3 (research + benchmark).
4. Báo cáo trung thực: đã chạy gì / chưa chạy gì / còn open question gì.
