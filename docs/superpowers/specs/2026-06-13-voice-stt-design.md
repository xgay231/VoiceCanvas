---
comet_change: voice-stt
role: technical-design
canonical_spec: openspec
archived-with: 2026-06-14-voice-stt
status: final
---

# Voice STT — 技术设计文档

## 概述

实现浏览器端持续语音监听 + 语音转文字（STT）管道。用户无需鼠标/键盘，系统自动检测语音段落，截断后发送到后端 mimo-v2.5-asr 模型进行识别，返回文本展示。

## 技术选型

| 组件           | 选型                            | 理由                                                                  |
| -------------- | ------------------------------- | --------------------------------------------------------------------- |
| 音频采集 + VAD | @ricky0123/vad-web (MicVAD)     | 一体化方案，同时处理音频采集和 Silero VAD 检测，无需单独 AudioWorklet |
| 音频编码       | 手写 WAV encoder (PCM + header) | 轻量无依赖，WAV 格式 mimo 原生支持                                    |
| ASR 模型       | mimo-v2.5-asr (非流式)          | 题目指定，OpenAI 兼容接口                                             |
| 后端客户端     | openai Python SDK               | mimo 兼容 OpenAI 接口格式                                             |
| 前端框架       | Vue 3 Composition API           | 项目已有基础                                                          |
| 后端框架       | FastAPI                         | 项目已有基础                                                          |

## 架构

```
浏览器 (Vue 3)                           后端 (FastAPI)
┌─────────────────────────────┐       ┌─────────────────────────┐
│  App.vue                    │       │  /api/asr               │
│    └─ VoiceControl.vue      │       │    ├─ 接收音频文件       │
│         ├─ useVoiceCapture   │       │    ├─ base64 编码        │
│         │   (MicVAD)        │       │    ├─ 调用 mimo-v2.5-asr │
│         │   ├─ 语音检测     │       │    └─ 返回识别文本       │
│         │   ├─ WAV 编码     │       └─────────────────────────┘
│         │   └─ 自动重试     │
│         └─ Result Display   │
│             (状态+文本)     │
└─────────────────────────────┘
```

## 核心模块

### 1. useVoiceCapture composable

**职责**：管理 MicVAD 生命周期、音频采集、WAV 编码、ASR 请求。

```ts
// 核心 API
const {
  status, // Ref<'idle' | 'listening' | 'speaking' | 'processing' | 'error'>
  results, // Ref<Array<{ text: string, timestamp: number }>>
  error, // Ref<string | null>
  start, // 启动监听
  stop, // 停止监听
} = useVoiceCapture();
```

**MicVAD 配置**：

```ts
const vad = await MicVAD.new({
  stream,
  // 静音截断：3 秒
  // 语音开始前缓冲：300ms（避免截掉开头）
  onSpeechStart: () => {
    status.value = "speaking";
  },
  onSpeechEnd: (audio: Float32Array) => {
    status.value = "processing";
    processAudio(audio);
  },
});
```

**音频处理流程**：

```
Float32Array (16kHz, MicVAD 输出)
  ↓ clamp [-1, 1] → scale to Int16
  ↓ prepend WAV header (44 bytes, 16kHz, 16-bit, mono)
  ↓ Blob → FormData
  ↓ POST /api/asr
  ↓ auto-retry on failure (3x, exponential backoff 1s/2s/4s)
```

### 2. WAV 编码工具

**职责**：将 Float32Array PCM 数据封装为 WAV 格式。

```ts
export function encodeWav(samples: Float32Array, sampleRate: number): Blob;
```

- 输入：Float32Array（-1.0 到 1.0），采样率（16000）
- 输出：Blob（WAV 格式）
- 实现：44 字节 RIFF/WAV header + 16-bit PCM 数据

### 3. 后端 ASR 路由

**端点**：`POST /api/asr`

**请求**：

- Content-Type: multipart/form-data
- Body: `audio` 字段（WAV 文件）

**响应**：

```json
{ "text": "识别结果", "success": true }
```

**错误响应**：

```json
{ "text": "", "success": false, "error": "错误描述" }
```

**实现**：

```python
@app.post("/api/asr")
async def transcribe(audio: UploadFile):
    audio_bytes = await audio.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    completion = client.chat.completions.create(
        model="mimo-v2.5-asr",
        messages=[{
            "role": "user",
            "content": [{
                "type": "input_audio",
                "input_audio": {
                    "data": f"data:audio/wav;base64,{audio_base64}"
                }
            }]
        }],
        extra_body={"asr_options": {"language": "zh"}}
    )
    return {"text": completion.choices[0].message.content, "success": True}
```

### 4. VoiceControl 组件

**职责**：UI 展示 + 调用 useVoiceCapture。

**UI 状态映射**：
| status | 显示 | 图标 |
|--------|------|------|
| idle | 未启动 | 🎤 |
| listening | 监听中... | 🎤 (动画) |
| speaking | 正在说话 | 🔴 |
| processing | 识别中... | ⏳ |
| error | 错误状态 | ⚠️ + 错误信息 |

**识别结果列表**：最新结果在底部，自动滚动。

## 错误处理

| 场景             | 前端行为                               | 后端行为            |
| ---------------- | -------------------------------------- | ------------------- |
| 麦克风权限拒绝   | 显示引导提示                           | N/A                 |
| VAD 模型加载失败 | 自动重试 3 次，失败显示错误            | N/A                 |
| ASR API 失败     | 自动重试 3 次 (1s/2s/4s)，显示错误状态 | 返回 500 + 错误信息 |
| 音频超时 (60s)   | 自动截断发送                           | 正常处理            |
| 音频超大 (>10MB) | 60s 上限间接控制                       | 返回 413 错误       |

## 音频参数

| 参数     | 值         | 来源             |
| -------- | ---------- | ---------------- |
| 采样率   | 16kHz      | MicVAD 内部固定  |
| 位深     | 16-bit PCM | WAV 编码时转换   |
| 声道     | 单声道     | MicVAD 固定      |
| 格式     | WAV        | mimo ASR 支持    |
| 静音截断 | 3 秒       | 用户确认         |
| 单段上限 | 60 秒      | 10MB base64 限制 |

## 依赖

### 前端新增

```json
{
  "@ricky0123/vad-web": "^0.0.22"
}
```

### 后端新增

```txt
openai>=1.0.0
python-multipart>=0.0.6
```

### 环境变量

- `MIMO_API_KEY`：mimo ASR API 密钥

## 目录结构

```
frontend/src/
├── components/
│   └── VoiceControl.vue          # 语音控制主组件
├── composables/
│   └── useVoiceCapture.ts        # MicVAD + WAV 编码 + 错误处理
├── utils/
│   └── wav-encoder.ts            # PCM → WAV 编码
└── App.vue                       # 入口，集成 VoiceControl

backend/
├── main.py                       # FastAPI + /api/asr 路由
└── requirements.txt              # 新增 openai, python-multipart
```
