## Context

VoiceCanvas 的现有链路是浏览器 VAD 捕获语音片段，前端编码 16kHz mono WAV 后调用 `/api/asr`，后端用 `mimo-v2.5-asr` 返回自然语言文本。项目已经有基础 Fabric 画布组件，但 ASR 文本仍只是展示结果，缺少从“用户意图”到“画布动作”的稳定中间层。

本 change 在后端补上语义理解层：

```text
WAV audio
  │
  ▼
/api/asr
  │
  ├─ mimo-v2.5-asr  ──► transcript text
  │
  └─ mimo-v2.5-pro  ──► structured drawing JSON
                           │
                           ▼
                    parse + validate + return
```

## Goals

- 让后端从 ASR 文本产出结构化绘图 JSON，而不是只返回自由文本。
- 通过 Prompt 约束和服务端校验共同提高输出稳定性。
- 保留原始转写文本，便于 UI 展示和调试。
- 对无法可靠执行的输入返回明确状态，例如 `clarification`、`no_op` 或 `unsupported`。
- 将 mimo-v2.5-pro 的原始模型消息输出到控制台日志，便于开发调试。

## Non-Goals

- 不实现完整前端绘图执行器。
- 不引入复杂多轮上下文或对象记忆系统。
- 不替换现有 ASR 模型。
- 不支持任意通用任务，只聚焦绘图/画布操作意图。

## Proposed API Shape

优先保持 `/api/asr` 作为单一语音入口，在现有返回基础上扩展字段：

```json
{
  "success": true,
  "text": "画一个蓝色圆形在画布中央",
  "drawing": {
    "version": "1.0",
    "type": "draw",
    "actions": [
      {
        "action": "create",
        "shape": "circle",
        "style": { "fill": "blue" },
        "position": { "preset": "center" }
      }
    ],
    "requires_clarification": false,
    "message": null
  }
}
```

当语义解析失败或不应执行时，`success` 只表示 ASR/API 总流程是否成功；`drawing.type` 表达绘图语义状态：

- `draw`: 可执行绘制/编辑动作。
- `clarification`: 用户意图依赖缺失上下文，需要追问。
- `no_op`: 输入与绘图无关或无需画布动作。
- `unsupported`: 用户请求属于绘图领域但当前 schema 不支持。
- `parse_error`: 模型输出无法解析或校验失败。

## Prompt Strategy

Prompt 应分为 system/developer 风格的稳定约束与 user 输入：

- 明确角色：只做画布绘图指令解析器。
- 明确输出：必须只返回 JSON 对象，禁止 Markdown、代码块、解释文本。
- 明确 schema：列出允许的顶层字段、枚举值、动作类型和字段含义。
- 明确不确定性策略：缺失对象引用或上下文时返回 `clarification`，不得伪造目标对象。
- 明确默认值策略：只有常识性安全默认值可填充；不确定位置/尺寸时使用 preset 或 null，而不是编造具体坐标。
- 明确非绘图输入：返回 `no_op`。

## Validation Strategy

服务端不信任模型输出：

1. 捕获 mimo-v2.5-pro 原始消息并 `print` 到控制台日志。
2. 尝试从消息中解析 JSON 对象。
3. 校验顶层字段、枚举值、actions 数组、必填字段。
4. 校验失败时返回 `drawing.type = "parse_error"` 和可诊断错误，不把未校验 JSON 当作可执行指令。

## Risks and Mitigations

- **模型输出包裹 Markdown 或解释文本**：Prompt 强约束 + 后端 JSON 提取/解析失败路径。
- **模型幻觉对象引用**：Prompt 规定上下文不足必须 `clarification`；校验层保留 message。
- **schema 过早复杂化**：第一版只覆盖 create/edit/no_op/unsupported/clarification/parse_error，复杂对象关系留给后续 change。
- **前端兼容性**：保留 `text` 字段，扩展新增 `drawing` 字段，降低对现有 UI 的破坏性。
