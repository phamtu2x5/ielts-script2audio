# Nguyên tắc kiến trúc

Tài liệu này cố định các nguyên tắc durable của hệ thống. Chi tiết vận hành: [`prompts/system-control.md`](prompts/system-control.md). Quyết định lớn: [`decisions/`](decisions/).

## 1. Ba plane

```text
CONTROL PLANE          TTS-NEUTRAL CONTRACTS         EXECUTION PLANE           VALIDATION PLANE
(Claude + domain)  →   (JSON manifests/requests)  →  (adapter + TTS backend) → (align / ASR / human)
```

| Plane | Trách nhiệm | Không làm |
|-------|-------------|-----------|
| **Control** | Validate, cast, normalise, risk, segment, manifest, release decision | Gọi vendor TTS trực tiếp; bịa nội dung |
| **Contracts** | Schema ổn định, ID ổn định, provenance | Logic provider-specific |
| **Execution** | Dịch request → backend; render segment | Đổi content, speaker, boundary, order, protected regions |
| **Validation** | Alignment, ASR, đo audio, assembly, human review | Sửa transcript im lặng |

## 2. Provider neutrality

- Domain core **không** import SDK/vendor TTS.
- Mọi output control plane là **TTS-neutral JSON** trước khi vào adapter.
- Backend có thể là open-weight, API, self-hosted, hoặc hybrid — **chưa chọn** cho đến Mode C có đủ evidence.
- Không chọn backend chỉ từ demo nhà cung cấp.
- Chi tiết ranh giới: [ADR-0002](decisions/ADR-0002-tts-adapter-boundary.md).

## 3. Tách `display_text` và `spoken_text`

```text
display_text = transcript gốc (bất biến với người nghe/đọc text)
spoken_text  = dạng TTS cần đọc (normalize an toàn)
```

- Mọi thay đổi có nguy cơ lệch nghĩa → `requires_human_approval: true`.
- Không sửa lỗi transcript im lặng: tạo validation issue + đề xuất + chờ human approval.

## 4. Nhãn provenance

| Nhãn | Ý nghĩa |
|------|---------|
| `[OFFICIAL]` | Đã xác minh từ nguồn IELTS.org / British Council (+ citation) |
| `[SAMPLE-OBSERVED]` | Quan sát từ sample chính thức; không phải quy định bắt buộc |
| `[DESIGN-PROPOSAL]` | Đề xuất kỹ thuật/sản xuất |
| `[USER-PROVIDED]` | Dữ liệu/cấu hình người dùng cung cấp |
| `[OPEN-QUESTION]` | Chưa đủ căn cứ |

Duration/timestamp không nguồn → `null` / `TBD`, không bịa số “hợp lý”.

## 5. Trạng thái thực thi trung thực

Mỗi bước pipeline mang một status:

```text
PLANNED | READY | EXECUTED | NOT_EXECUTED | FAILED | UNAVAILABLE | REQUIRES_HUMAN_REVIEW
```

- Không đánh `EXECUTED` nếu chưa chạy thật.
- Không tuyên bố đã render / align / ASR / human review khi chưa thực thi.

## 6. Bảo vệ answer-bearing

- Input có thể **không** có answer spans (optional — `[USER-PROVIDED]`).
- Khi có: tạo `protected_regions`; không cắt segment, pause sai, fade, clip, đổi voice, BGM/SFX, over-emphasise.
- Mục tiêu: `answer_salient` (không `answer_overemphasised`, không `answer_obscured`).
- Low-confidence pronunciation trên answer span = **release-blocking** cho tới khi xác nhận.
- Mọi answer span vẫn cần human listening review trước release (khi có validation plane).

## 7. Completeness và segmentation

- Mỗi utterance input xuất hiện đúng một lần, đúng thứ tự, đúng speaker.
- Không drop / merge / summarize / ellipsis.
- Không render cả Part thành một file TTS duy nhất.
- Không cắt giữa: họ tên, số+đơn vị, amount+currency, giờ+phút, code, spelling, answer phrase, contrast/correction quan trọng.

## 8. Adapter boundary (tóm tắt)

Adapter **được** map neutral request → API payload / SSML / phoneme / local args.  
Adapter **không được** đổi content, speaker identity, protected regions, segment boundaries, segment order.

Xem [ADR-0002](decisions/ADR-0002-tts-adapter-boundary.md).

## 9. Ngôn ngữ implementation

**Python 3.11+** — [ADR-0001](decisions/ADR-0001-implementation-language.md).

## 10. Kỷ luật thay đổi

1. Inspect repo  
2. Nêu assumptions / open questions  
3. Kế hoạch có biên  
4. Chờ approval trước implementation lớn  
5. Thay đổi nhỏ nhất có nghĩa  
6. Test / check liên quan  
7. Báo cáo đúng những gì đã chạy  
8. Kiến trúc lớn → ADR trong `docs/decisions/`  
9. Không mở rộng scope im lặng (P2 chỉ khi được yêu cầu)

## 11. Ưu tiên

| Mức | Nội dung |
|-----|----------|
| **P0** | Architecture, transcript integrity, speakers, TTS-neutral schema, normalisation, pronunciation, answer protection, duration provenance, segmentation, timeline, adapter abstraction, critical QA, truthful status |
| **P1** | SSML, alignment, ASR back-check, loudness, logging, retry, benchmark, licensing, cost, deployment |
| **P2** | UI, scoring, psychometric, question/distractor generation, band prediction |

Không dành nhiều công sức cho P2 hơn P0/P1.

## 12. Defaults đã chốt (MVP)

| Tham số | Giá trị | Provenance |
|---------|---------|------------|
| Locale spoken-form | `en-GB` (override per transcript) | `[USER-PROVIDED]` |
| Delivery profile | `content-only` | `[USER-PROVIDED]` |
| Answer-bearing | optional | `[USER-PROVIDED]` |
| Output format (request) | `wav` | `[DESIGN-PROPOSAL]` |
