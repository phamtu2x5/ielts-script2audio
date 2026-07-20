# Mục tiêu sản phẩm

## Vấn đề

Cần một pipeline **kiểm soát được và có thể kiểm chứng** để biến transcript IELTS-style Listening đã hoàn thiện thành audio luyện nghe. Các hệ thống TTS thông thường:

- gắn chặt một provider;
- dễ làm lệch answer-bearing phrases khi normalize;
- không enforce ràng buộc speaker theo Part;
- khó audit (ai quyết định gì, duration lấy từ đâu, đã chạy QA thật chưa).

## Mục tiêu

Xây hệ thống **provider-neutral**:

```text
transcript đã hoàn thiện
→ dữ liệu TTS-ready (manifest)
→ render segment qua adapter thay thế được
→ QA (tự động + human)
→ release có evidence
```

Claude đóng vai **control plane** (kiến trúc, validation, normalisation, segmentation, QA orchestration).  
TTS chỉ là **execution backend** có thể thay thế (open-weight / API / self-hosted / hybrid).

## Người dùng mục tiêu

- Người vận hành pipeline nội bộ (content / audio production)
- Agent (Claude) thao tác theo `docs/prompts/system-control.md`
- (Sau) kỹ sư tích hợp adapter TTS và tool QA

Không nhắm end-user UI trong các stage đầu.

## Thành công theo giai đoạn

### MVP 1 (Stage 0–2) — synthesis manifest

Từ một structured transcript hợp lệ, hệ thống tạo ra:

1. Báo cáo validation (speaker/part/completeness) có blocking issues rõ ràng  
2. `display_text` nguyên vẹn; `spoken_text` đã normalize an toàn (locale mặc định `en-GB`)  
3. Danh sách pronunciation risk (kèm confidence, `answer_bearing` nếu có)  
4. Segment phrase-safe (không cắt protected / answer-bearing)  
5. **Synthesis manifest** TTS-neutral (JSON), không phụ thuộc provider  

**Chưa yêu cầu:** render audio, alignment, ASR, human listening tool.

Defaults đã chốt `[USER-PROVIDED]`:

- Delivery profile: **content-only**
- Answer-bearing spans: **optional**
- Implementation language: **Python 3.11+**

### Giai đoạn sau

- Mode C: research + benchmark TTS (chưa chọn backend khi thiếu evidence)
- Mode D: adapter + render + retry
- Validation plane: forced alignment, ASR back-check, loudness, assembly, human review, release report

## Non-goals (ngoài phạm vi)

- Sinh transcript, câu hỏi, đáp án, distractor
- Band prediction, scoring, psychometric analysis
- UI sản phẩm (P2 — chỉ khi được yêu cầu)
- Tuyên bố “đề IELTS chính thức”
- Sao chép transcript/audio có bản quyền
- Mặc định hoặc khóa một TTS vendor trước benchmark

## Ràng buộc sản phẩm không thương lượng

- Bảo toàn dữ kiện, logic, speaker intent, answer-bearing phrases
- `display_text` bất biến; chỉ `spoken_text` được chuẩn hóa cho TTS
- Không bịa narrator wording, duration, timestamp
- Một content speaker giữ một voice identity trong suốt một Part
- Core domain độc lập provider ([ADR-0002](decisions/ADR-0002-tts-adapter-boundary.md))
- Trạng thái thực thi trung thực (`EXECUTED` chỉ khi đã chạy thật)

## Nguồn đặc tả

- Charter ngắn: [`CLAUDE.md`](../CLAUDE.md)
- Đặc tả vận hành đầy đủ: [`prompts/system-control.md`](prompts/system-control.md)
- Roadmap: [`roadmap.md`](roadmap.md)
