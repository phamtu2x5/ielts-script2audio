# Lab: inference against Stage 1–2 manifests

## Purpose

Test whether a TTS model can **use the prepared pipeline output**:

```text
transcript JSON
  → ielts-s2a prepare
  → synthesis manifest (requests[].spoken_text, voice_profile_id, …)
  → voice map
  → lab renderer
  → wav + report
```

Not production Stage 4. Not final model selection.

## Recommended first lab: Kokoro + Part 1

### Why Kokoro first
- Fixed voice IDs (no voice bank)
- en-GB voices available
- Light on Colab
- Clear map from `vp_spk_a` / `vp_spk_b`

### Files
| File | Role |
|------|------|
| `examples/part1_valid.json` | Stage-1 input |
| `outputs/part1_manifest.json` | Generate locally/Colab via prepare (gitignored under outputs/) |
| `configs/voice_maps/kokoro_en_gb_part1.json` | voice_profile_id → Kokoro id |
| `scripts/lab_render_kokoro_from_manifest.py` | Lab renderer |
| `notebooks/colab_kokoro_manifest_lab.ipynb` | Colab walkthrough |
| `checklist-stage1-2-compatibility.md` | What to verify |

## Colab steps (summary)

1. Runtime → GPU (L4/A100 if available).  
2. Clone repo: `https://github.com/phamtu2x5/ielts-script2audio.git` (notebook already uses this URL).  
3. Install:
   ```bash
   pip install -e ".[dev]" kokoro soundfile
   apt-get update && apt-get install -y espeak-ng
   ```
4. Prepare manifest:
   ```bash
   ielts-s2a prepare examples/part1_valid.json -o outputs/part1_manifest.json
   ```
5. Render:
   ```bash
   python scripts/lab_render_kokoro_from_manifest.py \
     --manifest outputs/part1_manifest.json \
     --voice-map configs/voice_maps/kokoro_en_gb_part1.json \
     --out-dir lab_audio/kokoro_part1
   ```
6. Listen + fill checklist.  
7. Write short notes in `notes-kokoro-part1.md` (create when done).

## Tracking từng câu audio vs nội dung (quan trọng)

Sau khi render, **đừng** chỉ mở lung tung các file `.wav`. Dùng một trong các cách sau — mỗi cách gắn **một audio** với **đúng** `display_text` / `spoken_text`.

### Cách 1 — Trong notebook (dễ nhất)

Cell **§5** sau khi render:

1. Hiện **bảng HTML**: mỗi hàng = segment + script + spoken + nút play.  
2. Bên dưới: in chi tiết + `Audio()` từng đoạn.  
3. Cell **§5b**: điền `reviews = { "seg_0001": {"content_match": "yes", "notes": "..."}, ... }` rồi lưu `segment_review_filled.json`.

### Cách 2 — File CSV (Excel / Google Sheets)

Renderer tự tạo:

`lab_audio/kokoro_part1/segment_tracking.csv`

Cột chính:

| Cột | Ý nghĩa |
|-----|---------|
| `segment_id` | id đoạn (khớp tên file wav) |
| `speaker_id` | ai nói |
| `backend_voice_id` | giọng Kokoro |
| `display_text` | chữ script gốc |
| `spoken_text` | chữ Stage-2 đưa TTS |
| `output_filename` | tên file wav |
| `human_content_match` | bạn điền: yes / partial / no |
| `human_notes` | ghi chú |

Cách dùng: mở CSV → nghe đúng `output_filename` → điền 2 cột human.

### Cách 3 — Terminal

```bash
python scripts/lab_show_segment_tracking.py \
  --report lab_audio/kokoro_part1/lab_render_report.json
```

In từng block: DISPLAY / SPOKEN / file — để tick tay.

### Cách đối chiếu “có đúng nội dung không”

Với **mỗi** hàng:

1. Đọc `display_text` (nội dung “đúng” của script — không sửa).  
2. Đọc `spoken_text` (cách máy được bảo đọc; có thể khác display, vd. spelling).  
3. Nghe audio.  
4. Hỏi:
   - Có **đúng speaker** (giọng A/B) không?  
   - Nội dung nghe được có **khớp ý** script không?  
   - Chỗ spelling/postcode: có bám `spoken_text` không?  
5. Ghi `yes` / `partial` / `no` + notes.  
6. **Không** sửa transcript cho “khớp audio”; nếu script sai → báo owner.

### Files sau một lần render đầy đủ

```text
lab_audio/kokoro_part1/
  seg_0001__bf_emma.wav
  ...
  lab_render_report.json          # machine report + full texts
  segment_tracking.csv            # sheet tracking
  segment_review_template.json    # template đánh giá
  segment_review_filled.json      # (sau khi bạn điền ở notebook §5b)
```

## Compatibility questions this lab answers

1. Can Kokoro take **`spoken_text`** from our manifest without us rewriting the script?  
2. Does **`voice_profile_id` → backend voice** work for 2 speakers?  
3. Do Stage-2 normalisations (spelling, postcode) **help** intelligibility?  
4. Any crash / empty audio / install blocker on Colab?  
5. Per segment: does audio **content** match display/spoken expectations?

## Status

| Item | Status |
|------|--------|
| Lab assets in repo | Ready |
| Audio render in this agent session | `NOT_EXECUTED` (needs Colab/GPU + kokoro install) |
| Final TTS selection | `not_selected` |
