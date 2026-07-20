# TTS evaluation criteria

Dùng cho so sánh ứng viên (desk research) và chấm benchmark (khi chạy).  
Thang điểm gợi ý: **0–3** mỗi tiêu chí (0 = không đạt / không rõ, 3 = mạnh).  
Tổng có trọng số — P0 nhân 2.

## 1. Tiêu chí và trọng số

| ID | Criterion | Weight | Ghi chú chấm |
|----|-----------|--------|--------------|
| C01 | Naturalness | ×2 | Nghe tự nhiên, không robotic |
| C02 | Intelligibility | ×2 | Nghe rõ chữ, đặc biệt answer spans |
| C03 | Speaker consistency | ×2 | Cùng voice_profile không “đổi người” giữa segment |
| C04 | Multi-speaker differentiation | ×2 | Part 3: nghe phân biệt không cần transcript |
| C05 | Accent fit (en-GB / neutral clear EN) | ×1 | Không bắt buộc multi-accent mọi Part |
| C06 | Pronunciation control | ×1 (now) / ×2 later | SSML/phoneme/lexicon **không** quyết prior hiện tại (API out-of-budget); chấm lab chủ yếu qua pre-norm `spoken_text` + clarity |
| C07 | Codes & numbers | ×2 | Spelling, phone, postcode, currency, time |
| C08 | Long-form stability | ×1 | Part 2/4 không drift giọng / artifacts nặng |
| C09 | Segment re-render consistency | ×2 | Render lại 1 segment khớp voice/prosody lân cận |
| C10 | Latency / throughput (batch) | ×1 | Phù hợp offline pipeline |
| C11 | Colab open-weight fit | ×2 | Chạy được notebook + CUDA L4/A100; API fit hạ residual |
| C12 | Privacy | ×1–2 | Nhân 2 nếu data không được rời máy |
| C13 | Licensing & commercial clarity | ×2 | 0 nếu mơ hồ / cấm commercial mà ta cần commercial |
| C14 | Cost predictability | ×1 | |
| C15 | Integration effort | ×1 | Adapter + voice inventory |
| C16 | Vendor lock-in risk | ×1 | 3 = dễ thay; 0 = khóa chặt |
| C17 | Consent / cloning ethics | ×2 | 0 nếu clone giọng người thật không consent |

## 2. Gate (hard fail)

Ứng viên **loại khỏi shortlist triển khai** nếu:

- G1: Không multi-voice đủ cho Part 3 (trừ khi hybrid voice bank rõ ràng).
- G2: Licensing commercial **không rõ hoặc cấm** mà use-case cần commercial.
- G3: Không thể segment re-render (chỉ full-chapter blob không tách).
- G4: Bắt buộc domain core phụ thuộc SDK (vi phạm ADR-0002) — *mitigate được bằng adapter thì không fail*.

## 3. Desk score vs lab score

| Phase | Cách chấm |
|-------|-----------|
| **Desk** (Stage 3 now) | Docs, license text, API docs, community reports — **không** thay listening test |
| **Lab** (sau) | Benchmark plan: human listening + optional ASR back-check |

Mọi điểm desk ghi: `evidence: docs | claim | unverified`.

## 4. Recommendation labels

| Label | Ý nghĩa |
|-------|---------|
| `research_only` | Theo dõi, chưa đủ điều kiện thử |
| `shortlist_lab` | Đủ để đưa vào benchmark lab |
| `pilot_adapter` | Sau lab đạt — được viết adapter thử |
| `final_selected` | **Cấm dùng** cho đến khi lab + licensing sign-off |
