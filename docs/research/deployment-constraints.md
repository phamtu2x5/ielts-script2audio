# Deployment & selection constraints (user-provided)

**Date:** 2026-07-20  
**Provenance:** `[USER-PROVIDED]` — cập nhật từ quyết định owner sau Stage 3 desk.

## OQ-06 — Deployment preference → **chốt tạm**

| Trước | Sau |
|-------|-----|
| undecided | **Colab-hosted open-weight inference** (không lấy máy local làm runtime chính) |

### Cách triển khai mong muốn

1. Code + config nằm trong **git repo** (push/pull).  
2. Chuẩn bị **notebook setup** (Colab) để clone/pull repo.  
3. **Inference / test TTS** chạy trên **Colab GPU** (L4 / A100), không yêu cầu cài model nặng trên máy cá nhân làm path chính.  
4. Control-plane (`ielts-s2a prepare`, schema, manifest) vẫn có thể chạy mọi nơi; **nặng TTS** = Colab.

### Hệ quả kiến trúc

- Adapter / lab scripts phải **chạy được trên Colab** (path, CUDA, download weights vào runtime Colab).  
- Không thiết kế “chỉ chạy được sau khi user tải full model về laptop”.  
- Artifact audio lab: lưu trên Colab / Drive / download có kiểm soát — **TBD** chi tiết sau; không giả định local `outputs/` là nơi duy nhất.

## OQ-07 — Privacy / budget / hardware → **chốt tạm**

| Hạng mục | Giá trị |
|----------|---------|
| Hardware | GPU **mạnh**: Colab **L4 / A100** |
| Budget API thương mại | **Thiếu kinh phí** → API **không** phải phương án triển khai chính hiện tại |
| Vai trò API (Azure/Polly/Google/ElevenLabs…) | **Research / tham chiếu** (SSML, catalog, so sánh tính năng) — **không** prior triển khai |
| Model size | **Được** cân nhắc model **hàng trăm triệu → tỷ tham số** (0.5B+), không giới hạn ở model ~80M |

### Privacy (vẫn mở một phần)

Transcript đẩy lên **Colab** (Google) — khác “API TTS vendor”, nhưng **không** còn “air-gapped local only”.  
Nếu sau này có transcript nhạy cảm: cần policy riêng `[OPEN-QUESTION]` (Colab data handling).

## Ưu tiên chọn TTS (cập nhật prior)

Thứ tự **prior chọn backend để lab / pilot** (không còn nghiêng Azure vì SSML):

1. **Open-weight**, chạy được trên **Colab L4/A100**  
2. **Đủ giọng + accent** cho constraint IELTS (Part 1–4, đặc biệt Part 3; en-GB / English rõ)  
3. **Ổn định segment re-render** + intelligibility codes (nhờ `spoken_text` + lab)  
4. **License** commercial-clear nếu cần commercial  
5. SSML / phoneme / lexicon — **cần thiết dài hạn**, nhưng **không** quyết prior chọn TTS **hiện tại** (vì API SSML mạnh đang out-of-budget)

## Script policy (nhắc lại)

Không tự sửa script/transcript/`display_text`. Có vấn đề → báo owner.
