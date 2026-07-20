# TTS backend requirements

Nguồn: pipeline Stage 1–2, `docs/ielts-audio-rules.md`, system-control §19.  
Provenance: `[DESIGN-PROPOSAL]` trừ khi ghi khác.

## 1. Bối cảnh sản phẩm

- Input: **synthesis manifest** TTS-neutral (segment + `spoken_text` + overrides + `voice_profile_id`).
- Output mong muốn (Stage 4+): audio segment WAV, có thể re-render từng segment.
- Deployment preference: **Colab open-weight** (L4/A100; repo + notebook) — `[USER-PROVIDED]` chốt tạm OQ-06; chi tiết `deployment-constraints.md`.
- Budget API thương mại: **thiếu** → API = research-only — `[USER-PROVIDED]` OQ-07.
- Hardware: GPU mạnh Colab → **được** xét model ~0.3B–0.5B+ (không chỉ model vài chục M).
- SSML/phoneme/lexicon: cần dài hạn; **không** quyết prior chọn TTS hiện tại (API SSML out-of-budget).

## 2. Functional requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Tổng hợp từ `spoken_text` (không tự rewrite transcript) | P0 |
| FR-02 | Multi-voice: map `voice_profile_id` → backend voice / speaker embedding | P0 |
| FR-03 | Tối thiểu ~4–6 giọng phân biệt được (Part 3 + narrator sau này) | P0 |
| FR-04 | English (en-GB ưu tiên; en-US chấp nhận được nếu có GB) | P0 |
| FR-05 | Pronunciation control: phoneme/SSML/lexicon **hoặc** chấp nhận pre-normalised text | P0 |
| FR-06 | Segment-level synthesis + selective re-render cùng voice | P0 |
| FR-07 | Ổn định giọng trong monologue dài (Part 2/4) | P0 |
| FR-08 | Intelligibility cao với postcode, spelling letter-by-letter, phone digits | P0 |
| FR-09 | Không bắt buộc BGM/SFX | P0 |
| FR-10 | Output WAV (hoặc convert lossless → WAV) | P1 |
| FR-11 | Optional streaming (không bắt buộc MVP render) | P2 |

## 3. Non-functional requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-01 | Có thể gắn qua **adapter** (ADR-0002), không leak vào domain core | P0 |
| NFR-02 | Licensing / commercial use **rõ** trước release | P0 |
| NFR-03 | Privacy: nếu transcript nhạy cảm → ưu tiên local/self-hosted | P1 (tùy OQ-07) |
| NFR-04 | Cost dự đoán được (per char / per hour GPU) | P1 |
| NFR-05 | Latency chấp nhận được cho batch offline (không real-time exam) | P1 |
| NFR-06 | Vendor lock-in thấp (neutral manifest đã giảm một phần) | P1 |
| NFR-07 | Tài liệu voice inventory + consent (nếu clone) | P0 nếu dùng cloning |

## 4. Constraints từ IELTS-style audio

- Part 1 dialogue (2 speakers), Part 2 mono, Part 3 2–4 speakers, Part 4 academic mono.
- Answer-bearing spans: không được méo / nuốt / over-emphasise (QA Stage 5).
- Một speaker = một voice identity trong Part.
- Accent tự nhiên; không stereotype; không pitch-shift cực đoan.

## 5. Out of scope cho chọn backend

- Sinh transcript / câu hỏi.
- UI.
- Band scoring.

## 6. Success cho Stage 3 (research only)

Stage 3 **thành công** khi có:

1. Requirements + criteria (file này + evaluation criteria).
2. Candidate notes có licensing/privacy/cost **desk-level**.
3. Benchmark plan map được sang fixtures Stage 2.
4. Shortlist có **recommendation status ≠ final** nếu chưa chạy benchmark.

**Không** yêu cầu: audio đã render, vendor đã ký, adapter đã code.
