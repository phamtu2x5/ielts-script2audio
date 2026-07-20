# Quy tắc audio IELTS-style

Tài liệu gom các ràng buộc liên quan format nghe IELTS-style dùng trong pipeline.  
**Không** trình bày đặc điểm sample hay quyết định kỹ thuật như quy định IELTS chính thức khi chưa xác minh.

Nguồn vận hành chi tiết: [`prompts/system-control.md`](prompts/system-control.md).

## 1. Content speakers theo Part

`[DESIGN-PROPOSAL]` — ràng buộc hệ thống (align thông lệ IELTS Listening format; **chưa** gắn `[OFFICIAL]` trong repo này):

| Part | Content speakers | Ghi chú |
|------|------------------|---------|
| Part 1 | đúng **2** | Dialogue |
| Part 2 | đúng **1** | Monologue |
| Part 3 | **2–4** | Discussion |
| Part 4 | đúng **1** | Academic monologue |

- **Narrator không** tính vào `content_speaker_count`.
- Phải phân biệt: `audio_voice_count`, `content_speaker_count`, `narrator_voice_count`.

**Validation fail khi:**

- Part 1 ≠ 2 content speakers  
- Part 2 hoặc 4 có content speaker thứ hai  
- Part 3 &lt; 2 hoặc &gt; 4 content speakers  
- Narrator bị đếm như content speaker  
- Speaker label không nhất quán  
- Transcript không khớp Part number  

## 2. Casting và voice consistency

`[DESIGN-PROPOSAL]`

- Một speaker → **một** voice identity xuyên suốt Part.
- Narrator khác rõ content voices.
- Accent tự nhiên, dễ hiểu; không phóng đại; không stereotype.
- Không pitch-shifting cực đoan.
- Không bắt buộc mỗi Part một accent khác nhau.
- **Timbre** là yếu tố phân biệt chính; rate / energy / formality chỉ hỗ trợ nhẹ.

### Part 3 (3–4 speakers) — thứ tự ưu tiên phân biệt

1. Role và formality  
2. Timbre  
3. Speaking rate / energy nhẹ  
4. Accent nhẹ nếu backend hỗ trợ tự nhiên  

**Câu hỏi bắt buộc:** *Người nghe có nhận ra speaker hiện tại mà không nhìn transcript không?*  
Nếu không ổn định → casting chưa đạt (release-blocking khi tới giai release).

### Voice inventory hạn chế

Fallback: khác timbre → khác role/formality → chỉnh nhẹ rate/energy → accent nhẹ tự nhiên → yêu cầu thêm voice.  
Không che giấu thiếu voice; không tái sử dụng voice nếu gây nhầm speaker.

## 3. Bảo toàn transcript

Tuyệt đối không đổi (trong `display_text` và logic):

- dữ kiện, tên riêng, địa điểm, ngày/giờ, tiền, điện thoại, postcode, booking code;
- measurements / đơn vị;
- answer-bearing words;
- thứ tự thông tin, quyết định cuối, quan điểm / intent speaker;
- quan hệ logic giữa lượt nói.

**Chỉ** được đụng trong `spoken_text` để: mở rộng abbreviation (khi chắc), số → dạng đọc, spelling, pronunciation override, phrase break, sparse prosody, segment kỹ thuật, dấu câu phục vụ TTS.

Lỗi transcript phát hiện được → validation issue + đề xuất; **không** tự sửa; cần human approval.

### Completeness

- Mỗi utterance input xuất hiện đúng một lần trong output TTS-ready  
- Không bỏ / gộp / tóm tắt / thay bằng `...`  
- Giữ thứ tự và speaker attribution  
- Output dài → batch liên tục với `event_id` ổn định + `first_event_id` / `last_event_id` / `next_event_id`  

## 4. Spoken-form normalisation

`[DESIGN-PROPOSAL]` + locale mặc định `[USER-PROVIDED]`: **en-GB** (override per transcript).

Mỗi utterance:

```text
display_text
spoken_text
normalisation_changes
pronunciation_overrides
requires_human_approval
```

Xử lý cẩn thận: tên + spelling, postcode, phone, booking code, date/time, currency, decimal/fraction/%, measurements, room/bus/route, abbreviations, acronyms, homographs.

Quy tắc:

- Không đổi thứ tự ngày/tháng nếu locale chưa rõ  
- Không đọc phone/code như số nguyên  
- Không tách số khỏi đơn vị  
- Chỉ expand abbreviation khi chắc chắn  
- Không tự dùng “double”/“triple” nếu chưa có convention (`[OPEN-QUESTION]` OQ-08)  
- Đa cách đọc hợp lệ ảnh hưởng nghĩa → human review  

## 5. Pronunciation risk

Mỗi risk cần: `risk_id`, `token`, `category`, forms, hints, `confidence` (`high|medium|low`), `answer_bearing`, `requires_human_review`.

Ưu tiên: tên người/địa danh/tổ chức, postcode, phone, booking code, date/time/money/measurements, acronyms, homographs, answer-bearing phrases.

**Low-confidence + answer-bearing = release-blocking** cho tới khi xác nhận.

## 6. Sparse prosody

Chỉ annotate khi ảnh hưởng intelligibility, turn-taking, correction, contrast, discourse boundary, final decision, answer-bearing, natural phrasing.

Nhãn tương đối ưu tiên: `brief`, `normal_turn_gap`, `clause_boundary`, `section_boundary`.  
Không cần → `"prosody": null`.  
Không annotate pitch/emotion/rate cho mọi câu.

## 7. Answer-bearing protection

- Answer spans trong input: **optional** `[USER-PROVIDED]`.
- Khi có → `protected_regions`.
- Cấm: cắt trong span, pause sai, fade đè, clipping, mất đầu/cuối từ, đổi voice, BGM, SFX, làm chậm bất thường, nhấn quá mức, làm đáp án “rõ bất thường”.
- Mục tiêu: `answer_salient` (không overemphasised, không obscured).
- Human listening review bắt buộc trước release cho mọi answer span (khi có validation plane).

## 8. Narrator và exam-control

`[DESIGN-PROPOSAL]`

Tách exam-control events khỏi content events. Có thể gồm: test/part intro, question-range instruction, preview, question-group transition, checking period, part transition, test-end.

Narrator: rõ, trung tính, nhất quán, khác content, không clue.

**Không tự tạo narrator wording** nếu script chưa có → `[OPEN-QUESTION]`.

MVP delivery profile: **content-only** — không bắt buộc shell exam đầy đủ.

## 9. Segmentation

Không render cả Part một file TTS.

Tách: narrator segments (nếu có), speaker turns, phrase-safe subsegments, silence/transition events.

**Không chia segment:**

- giữa tên và họ  
- giữa số và đơn vị / amount và currency / giờ và phút  
- bên trong booking code / spelling sequence / answer-bearing phrase  
- tại correction hoặc contrast quan trọng  
- tại vị trí làm đổi nghĩa  

## 10. Duration và timeline

Mọi duration cần `source_type`: `OFFICIAL | SAMPLE_OBSERVED | DESIGN_PROPOSAL | USER_PROVIDED` (hoặc `OPEN_QUESTION`).

Không nguồn → `duration_ms = null` (hoặc `TBD`); không timestamp giả; không số tròn “có vẻ đúng”.

Pause trong speech: ưu tiên nhãn tương đối trước khi map ms (sau khi có backend/convention).

Không BGM; SFX mặc định tắt.

Không giả định mọi Part cùng cấu trúc timeline.

## 11. Release-blocking (khi tới validation plane)

- Sai dữ kiện / sai answer-bearing word / sai speaker  
- Voice switch ngoài ý muốn  
- Pronunciation ảnh hưởng đáp án  
- Part 3 không phân biệt được speaker  
- Answer bị che hoặc bị nhấn quá mức  
- Duration không nguồn nhưng bị coi là official  
- Licensing / voice consent chưa rõ  
- Low-confidence answer pronunciation chưa xác nhận  

## 12. Machine-readable output

JSON hợp lệ: không comment, không `...`, `null`/`true`/`false` thật, ID ổn định, không reference mồ côi, giữ utterance count và order.
