# Architecture Decision Records (ADR)

Thư mục này lưu các quyết định kiến trúc có ý nghĩa. Mọi thay đổi lớn về ngôn ngữ, ranh giới module, contract TTS, hay packaging nên có ADR.

## Mục lục

| ADR | Tiêu đề | Status |
|-----|---------|--------|
| [ADR-0001](ADR-0001-implementation-language.md) | Implementation language | Accepted |
| [ADR-0002](ADR-0002-tts-adapter-boundary.md) | TTS adapter boundary | Accepted |

## Khi nào viết ADR

- Chọn hoặc đổi implementation language / runtime
- Đổi ranh giới control plane ↔ execution plane
- Đổi schema contract công khai (breaking)
- Chọn TTS backend (sau Mode C) hoặc chiến lược multi-backend
- Đổi mô hình packaging, deployment, hay data store cốt lõi

Không cần ADR cho: typo docs, refactor nội bộ không đổi contract, thêm test thuần túy.

## Mẫu ADR

```markdown
# ADR-NNNN: Tiêu đề ngắn

- **Status:** Proposed | Accepted | Superseded by ADR-XXXX | Deprecated
- **Date:** YYYY-MM-DD
- **Deciders:** …

## Context

Vấn đề / lực đẩy cần quyết định.

## Options considered

1. …
2. …

## Decision

Quyết định cụ thể.

## Consequences

- Tích cực:
- Tiêu cực / trade-off:
- Follow-up:

## References

- Links tới system-control, issues, research notes
```

## Quy ước đặt tên

```text
ADR-NNNN-kebab-case-title.md
```

Số tăng dần, không tái sử dụng số đã public.
