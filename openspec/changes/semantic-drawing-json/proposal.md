## Why

VoiceCanvas 当前后端只负责把语音转写为自然语言文本，前端画布无法直接消费自由文本来执行稳定的绘图操作。为支持“语音驱动画布”的下一步能力，需要在后端接入 `mimo-v2.5-pro` 进行语义理解与指令拆解，并将用户话语转换为可校验、可诊断、可前端执行的结构化绘图 JSON。

## What Changes

- 在后端引入语义理解/指令拆解能力：基于 ASR 文本调用 `mimo-v2.5-pro`，输出结构化绘图指令 JSON。
- 设计稳定 Prompt 与输出约束，要求模型只输出符合约定 schema 的 JSON，不输出解释性自由文本。
- 定义后端返回契约，保留原始转写文本，并返回解析后的绘图语义结果、失败原因或澄清请求。
- 增加服务端 JSON 解析与基础校验：模型输出非 JSON、字段缺失、动作不支持时不得把脏数据传给前端。
- 将模型原始消息输出到后端控制台日志，便于开发阶段调试 mimo-v2.5-pro 的结构化输出稳定性。
- 不替换现有 `mimo-v2.5-asr` 语音转文字能力；ASR 仍保持当前音频输入契约。

## Capabilities

### New Capabilities

- `semantic-drawing-json`: 将自然语言绘图指令解析为结构化绘图 JSON，包括绘制、编辑、澄清、无操作/不支持等结果类型。

### Modified Capabilities

- 无。

## Impact

- 后端 API：主要影响 [backend/main.py](backend/main.py) 的 `/api/asr` 调用链和响应结构；可能新增内部 helper、Prompt 常量、schema 校验逻辑。
- 模型依赖：新增对 `mimo-v2.5-pro` 的 OpenAI-compatible chat completions 调用，继续复用 `MIMO_API_KEY` 与 `MIMO_BASE_URL`。
- 前端契约：后续前端 Fabric 画布可消费结构化 JSON；本 change 不实现完整前端绘图执行器。
- 调试与可观测性：后端控制台日志会输出 mimo-v2.5-pro 原始消息，用于验证 Prompt 与 schema 稳定性。
