## Overview

本变更把现有“语音识别文本展示”扩展为“识别文本 → 独立语义解析接口 → drawing envelope → Fabric.js 执行”的闭环。后端继续负责把自然语言转换为受验证的结构化 drawing envelope；前端只消费该契约并执行白名单内的基础创建动作。

## Architecture Decisions

### Use a standalone drawing interpretation endpoint

前端 SHALL 在拿到 ASR transcript 后调用独立绘图解析接口，而不是把 `/api/asr` 的 `text` 字段当作 JSON 解析。这样保留文本识别展示语义，也允许未来支持键盘输入或其他文本来源复用同一绘图解析能力。

### Keep drawing execution in the canvas boundary

Fabric.js 对象创建 SHALL 封装在 `DrawingCanvas` 或其相邻执行模块中。语音控制组件只负责传递 transcript、展示解析消息和调用画布公开入口，不直接构造 Fabric 对象。

### Execute only supported create actions

第一版前端 SHALL 只执行 `drawing.type === "draw"` 且 `action === "create"` 的基础图形动作。支持的基础形状以现有后端契约为准，至少覆盖 rectangle、circle、text、line；未知 action 或未知 shape SHALL 被跳过并以消息提示呈现，不导致页面崩溃。

### Preserve message-first non-draw behavior

当 drawing envelope 表示 clarification、no_op、unsupported、parse_error 或 semantic_error 时，前端 SHALL 显示 envelope 的 `message`，不新增、删除或修改画布对象。

## Data Flow

```text
MicVAD speech segment
  → /api/asr
  → transcript text
  → standalone drawing interpretation endpoint
  → drawing envelope
  ├─ type=draw + create actions → DrawingCanvas executes Fabric object creation
  └─ non-draw/error type         → Voice UI displays message, canvas unchanged
```

## Contract Notes

- Request body SHOULD submit the transcript text; canvas context remains optional and is not required for this first execution path.
- Response body SHOULD preserve the drawing envelope fields: `version`, `type`, `actions`, `requires_clarification`, `message`.
- Frontend SHALL treat backend output as data, not executable code, and SHALL map only known fields into Fabric.js options.

## Open Questions for Build

- Confirm the final endpoint path from existing backend code before implementation.
- Confirm the exact shape names emitted by the current prompt/validator and keep frontend shape mapping aligned.
- Decide whether skipped unsupported actions should produce one aggregate message or per-action feedback in UI.
