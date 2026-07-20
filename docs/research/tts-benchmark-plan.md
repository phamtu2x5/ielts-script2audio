# TTS benchmark plan

**Status:** `PLANNED` — chưa chạy audio (`NOT_EXECUTED`).  
**Mục tiêu:** So sánh shortlist trên **cùng** synthesis manifest, không so demo marketing.

## 1. Nguyên tắc

1. Input duy nhất: output `ielts-s2a prepare` (TTS-neutral requests).  
2. Mỗi backend: một adapter tạm / script — **không** sửa `spoken_text` khác nhau giữa backends (trừ transform bắt buộc của adapter, log lại).  
3. Cùng `voice_profile_id` → inventory map cố định per backend.  
4. Ghi `render_status` trung thực; failure không xóa case.  
5. Human listening là trọng tài chính cho C01–C04, C07–C09; ASR chỉ phụ.

## 2. Corpus (tối thiểu)

### 2.1 Fixtures có sẵn

| ID | Source | Part | Focus |
|----|--------|------|-------|
| B-P1 | `examples/part1_valid.json` → prepare | 1 | Dialogue 2 spk, spelling, postcode, answer spans |
| B-P2 | `examples/part2_valid.json` | 2 | Short monologue consistency |
| B-P3 | `examples/part3_valid.json` | 3 | 3-way differentiation |
| B-P4 | `examples/part4_valid.json` | 4 | Academic mono |

### 2.2 Cases bổ sung (tạo khi lab — chưa cần code ngay)

| ID | Content | Tests |
|----|---------|-------|
| B-NUM | Dates, times, currency, measurements, % | C07 |
| B-CODE | Phone, booking code, postcode variants | C07, C06 |
| B-CORR | Correction / contrast (“not 15, 50”) | C01, C02 |
| B-ANS | Dense answer-bearing spans | C02, protection |
| B-LONG | Part 2-style 2–3 min mono (synthetic) | C08 |
| B-RERENDER | Re-synth middle segment of B-P1 | C09 |

Có thể thêm JSON dưới `examples/benchmark/` sau — **TBD**.

## 3. Protocol mỗi backend

1. `prepare` fixture → manifest JSON (commit hoặc hash).  
2. Map `vp_*` → backend voice ids (bảng inventory).  
3. Render mỗi `requests[]` → `outputs/bench/{backend}/{segment_id}.wav`.  
4. Log: latency_ms, char_count, error, seed/settings.  
5. Optional: concatenate Part for listening (không dùng 1-shot TTS cả Part).  
6. Score sheet theo [tts-evaluation-criteria.md](tts-evaluation-criteria.md).

## 4. Human listening rubric (rút gọn)

Listener (1–2 người) với transcript ẩn lần 1:

| Question | Related |
|----------|---------|
| Nghe rõ từng answer span không? | C02 |
| Đoán được ai đang nói (Part 3) không? | C04 |
| Có đoạn nuốt chữ / cut / robot không? | C01–C02 |
| Postcode / spelling có follow được không? | C07 |
| Re-render có “lạc giọng” không? | C09 |

Ghi `pass / borderline / fail` + note — không chỉ số điểm marketing.

## 5. Automated helpers (optional, Stage 5 tools)

- Duration vs spoken length sanity.  
- ASR back-transcript vs `display_text` / `spoken_text` (không phải ground truth duy nhất).  
- Peak clipping detect.

Status hiện tại: tools **UNAVAILABLE** trong repo.

## 6. Decision rule sau lab

- Chỉ backend có **G-gates pass** + không fail P0 criteria mới vào `pilot_adapter`.  
- Nếu không ai đạt codes (C07): ưu tiên backend SSML mạnh **hoặc** cải normaliser — ghi rõ trade-off.  
- **Final_selected** chỉ sau: lab notes + license sign-off + OQ-06/07.

## 7. Effort estimate (order-of-magnitude)

| Task | Effort |
|------|--------|
| Inventory maps + 1 adapter smoke mỗi shortlist | 0.5–2 ngày / backend |
| Full corpus B-P1…P4 + listen | 0.5–1 ngày |
| B-NUM/B-CODE extras | 0.5 ngày |
| Write-up scores | 0.5 ngày |

## 8. Explicit non-goals of first lab

- Không tối ưu prosody emotion.  
- Không multi-language.  
- Không production SLA.  
