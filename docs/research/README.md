# TTS research (Mode C)

Tài liệu Stage 3 — **nghiên cứu backend TTS**, chưa chọn vendor cuối cùng.

| File | Nội dung |
|------|----------|
| [deployment-constraints.md](deployment-constraints.md) | OQ-06/07: Colab L4/A100, open-weight, API research-only |
| [tts-requirements.md](tts-requirements.md) | Yêu cầu từ pipeline IELTS script→audio |
| [tts-evaluation-criteria.md](tts-evaluation-criteria.md) | Tiêu chí chấm điểm / so sánh |
| [tts-candidates.md](tts-candidates.md) | Ứng viên open-weight (prior) + API research-only |
| [tts-benchmark-plan.md](tts-benchmark-plan.md) | Kế hoạch benchmark (chưa chạy) |
| [tts-shortlist.md](tts-shortlist.md) | Shortlist + evidence còn thiếu + recommendation status |
| [voice-inventory-deep-dive.md](voice-inventory-deep-dive.md) | **Voice inventory** Type F/Z; Kokoro/CosyVoice/F5 counts; IELTS Part fit |
| [candidates-qwen-fish-chatterbox-fixed-voice.md](candidates-qwen-fish-chatterbox-fixed-voice.md) | Qwen3-TTS, Fish S2 Pro, Chatterbox, MeloTTS; fixed-voice survey |
| [candidates-parler-orpheus-melo-voxtral.md](candidates-parler-orpheus-melo-voxtral.md) | Parler Mini v1.1, Orpheus, MeloTTS, Voxtral-4B-TTS-2603 |
| [lab/README.md](lab/README.md) | **Inference lab** vs Stage 1–2 manifests (Kokoro first) |

## Quy tắc Mode C

- Không chọn backend chỉ từ demo nhà cung cấp.
- Không đánh `final selection` khi thiếu benchmark evidence.
- Mọi claim licensing/commercial phải verify lại trước integrate (Stage 4).
- Adapter boundary: [ADR-0002](../decisions/ADR-0002-tts-adapter-boundary.md).

## Trạng thái

| Hạng mục | Status |
|----------|--------|
| Requirements / criteria | Drafted Stage 3 |
| Candidate desk research | Drafted Stage 3 |
| Live benchmark / listening test | `NOT_EXECUTED` |
| Final TTS backend | **not_selected** |
