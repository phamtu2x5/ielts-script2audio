# ADR-0002: TTS adapter boundary

- **Status:** Accepted
- **Date:** 2026-07-20
- **Deciders:** Project owner (Phạm Văn Tư), Claude (control-plane design session)

## Context

Hệ thống phải **provider-neutral**: Claude/control plane quyết định nội dung và cấu trúc; TTS backend chỉ thực thi. Nếu domain code gọi thẳng API vendor hoặc nhúng SSML provider-specific, sẽ:

- khóa vendor sớm (trái non-negotiable);
- khó benchmark nhiều backend;
- dễ để backend “tự quyết” speaker/boundary/pronunciation.

Cần ranh giới cứng giữa **TTS-neutral contracts** và **execution plane**.

## Options considered

1. **Neutral JSON contract + thin adapter (chọn)**  
   Control plane chỉ emit request/manifest trung lập; mỗi backend một adapter thuần dịch.

2. **SSML-first canonical format**  
   Một SSML dialect làm lingua franca — vẫn nghiêng vendor/feature subset; khó map 1-1 sang model local không SSML.

3. **Domain gọi thẳng SDK vendor**  
   Nhanh short-term; lock-in và vi phạm control/execution separation.

4. **Plugin per-provider với logic normalisation riêng**  
   Rủi ro mỗi provider normalize khác nhau → lệch `spoken_text` / answer spans.

## Decision

1. **Mọi output control plane** (segment, pronunciation overrides, casting abstract, synthesis requests) là **TTS-neutral JSON** trước khi chạm backend.
2. **`TTSAdapter`** là ranh giới duy nhất được phép biết chi tiết provider.
3. Adapter **được phép** chuyển neutral request thành:
   - API payload;
   - SSML / phoneme format;
   - model-specific parameters;
   - local inference arguments.
4. Adapter **không được** tự ý thay đổi:
   - nội dung (`display_text` / `spoken_text` semantics);
   - speaker identity / `voice_profile_id` mapping ngoài bảng inventory đã cấu hình;
   - protected regions;
   - segment boundaries;
   - segment order;
   - release status hay answer-bearing policy.
5. `voice_profile_id` là ID trừu tượng của control plane; `backend_voice_id` chỉ xuất hiện ở lớp adapter/inventory mapping.
6. Domain packages **không** import SDK vendor; chỉ package adapter (hoặc extras optional) được phụ thuộc provider.
7. Contract tests dùng **fake adapter** để khóa invariant trên, độc lập backend thật.

Shape request trung lập (tham chiếu system-control §18):

```json
{
  "request_id": "string",
  "segment_id": "string",
  "speaker_id": "string",
  "voice_profile_id": "string",
  "display_text": "string",
  "spoken_text": "string",
  "locale": null,
  "accent_target": null,
  "pronunciation_overrides": [],
  "prosody": null,
  "protected_region_ids": [],
  "output_format": "wav",
  "sample_rate": null,
  "status": "READY"
}
```

MVP 1 **dừng ở manifest** — implement adapter thật thuộc Stage 4; ADR này chốt **boundary** trước để Stage 1–2 không leak provider.

Provenance: `[DESIGN-PROPOSAL]` + phê duyệt session 2026-07-20 `[USER-PROVIDED]`.

## Consequences

### Tích cực

- Core có thể hoàn thành validation → manifest mà không chọn vendor.
- Mode C so sánh backend trên cùng contract.
- Dễ selective re-render và audit (request ổn định, adapter chỉ dịch).

### Tiêu cực / trade-off

- Một số tính năng provider-specific (emotion SSML phong phú, cloning API…) chỉ vào qua extension fields **không** được domain bắt buộc; cần versioning cẩn thận.
- Adapter phải chịu trách nhiệm map lỗi/retry ở ranh giới execution, không đẩy decision ngược vào transcript.

### Follow-up

- Stage 2: `ManifestBuilder` chỉ emit neutral requests.
- Stage 4: adapter thật + fake adapter tests; inventory mapping document.
- Stage 3: không được “lách” bằng cách nhúng vendor ID vào domain schema.

## References

- [`docs/architecture-principles.md`](../architecture-principles.md) §2, §8
- [`docs/prompts/system-control.md`](../prompts/system-control.md) §1, §18, §19
- [`docs/roadmap.md`](../roadmap.md) — Stage 2–4
- [`CLAUDE.md`](../../CLAUDE.md) — provider-neutral non-negotiables
