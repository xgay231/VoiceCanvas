## Why

VoiceCanvas 需要实现纯语音控制能力，让用户在完全不使用鼠标和键盘的情况下与应用交互。本阶段聚焦于语音转文字（STT）管道的搭建：浏览器端持续监听麦克风，智能检测语音段落，截断后发送到后端进行 ASR 识别，返回识别文本展示给用户。

## What Changes

- 新增前端语音采集模块：使用 AudioWorklet 持续采集 PCM 原始音频数据
- 新增前端 VAD（语音活动检测）：集成 Silero VAD（ONNX 模型，浏览器端推理），自动检测语音开始/结束
- 新增前端 WAV 编码：将 PCM 数据封装为 WAV 格式（mimo ASR 要求）
- 新增后端 ASR 接口：接收音频文件，base64 编码后调用 mimo-v2.5-asr 模型
- 新增前端识别结果展示界面

## Capabilities

### New Capabilities

- `voice-capture`: 浏览器端音频采集、VAD 语音活动检测、PCM 录制与 WAV 编码
- `speech-recognition`: 后端 mimo-v2.5-asr API 集成，音频上传与识别结果返回

### Modified Capabilities

（无，项目为全新功能）

## Impact

- **前端新增**：AudioWorklet processor、VAD 模型加载、WAV 编码工具、语音控制主组件
- **后端新增**：ASR API 路由（`/api/asr`）、mimo API 客户端集成
- **新依赖**：
  - 前端：`@ricky0123/vad-web`（Silero VAD）
  - 后端：`openai` Python SDK（mimo 兼容 OpenAI 接口格式）
- **环境变量**：后端需要 `MIMO_API_KEY`
- **音频限制**：base64 编码后 ≤ 10MB，格式为 WAV
