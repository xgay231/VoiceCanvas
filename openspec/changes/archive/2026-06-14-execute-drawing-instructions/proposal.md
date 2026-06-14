## Why

VoiceCanvas 已能将语音识别结果转换为结构化绘图语义，但前端仍只展示文本，无法消费这些 JSON 指令来驱动画布绘制。用户需要从语音到画布图形的闭环：文本识别后通过独立语义解析接口获取绘图指令，并在 Fabric.js 画布上执行基础创建动作。

## What Changes

- 前端在获得识别文本后调用独立绘图解析接口，读取后端返回的 drawing envelope。
- DrawingCanvas 暴露绘图指令执行入口，将受支持的 `create` actions 映射到 Fabric.js 基础图形。
- 前端对 `clarification`、`no_op`、`unsupported`、`parse_error`、`semantic_error` 等非绘制结果显示后端 message，且不改动画布。
- 后端独立绘图解析接口保持稳定返回契约，供前端在非音频上传场景下提交文本并获取 drawing envelope。
- 本次不实现编辑已有对象、撤销/重做、清空画布、复杂布局、多轮澄清 UI 或画布状态持久化。

## Capabilities

### New Capabilities

- None

### Modified Capabilities

- `semantic-drawing-json`: 明确独立绘图解析接口作为前端绘图执行的数据来源，并约束非绘制结果的 message 返回。
- `drawing-canvas`: 增加消费结构化绘图指令并执行基础 Fabric.js 创建动作的前端画布行为。

## Impact

- Frontend: `VoiceControl`/语音结果链路、`DrawingCanvas` Fabric.js 执行入口、可能新增前端指令解析/执行辅助模块。
- Backend: 独立绘图解析 API 的请求/响应契约，必要时调整 prompt 或 response shape 以满足前端消费。
- API: 前端将以识别文本调用独立 endpoint，而不是把 `/api/asr` 的 `text` 当作 JSON 字符串解析。
- Tests/verification: 需要覆盖基础 create 动作、非绘制结果提示、未知 action 防崩溃，以及现有识别文本展示不回退。
