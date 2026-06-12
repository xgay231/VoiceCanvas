## 架构总览

```
浏览器 (Vue 3)                           后端 (FastAPI)
┌─────────────────────────────┐       ┌─────────────────────────┐
│  App.vue                    │       │  /api/asr               │
│    └─ VoiceControl.vue      │       │    ├─ 接收音频文件       │
│         ├─ AudioWorklet     │       │    ├─ base64 编码        │
│         │   (PCM 采集)      │       │    ├─ 调用 mimo-v2.5-asr │
│         ├─ Silero VAD       │       │    └─ 返回识别文本       │
│         │   (语音检测)      │       └─────────────────────────┘
│         ├─ WAV Encoder      │
│         │   (格式封装)      │
│         └─ Result Display   │
│             (文本展示)      │
└─────────────────────────────┘
```

## 技术选型

### 前端

| 组件 | 选型 | 理由 |
|------|------|------|
| 音频采集 | Web Audio API + AudioWorklet | 直接获取 PCM 数据，避免 MediaRecorder 输出 webm 格式问题 |
| VAD | @ricky0123/vad-web (Silero VAD) | 浏览器端 ONNX 推理，ML 级别准确率，零服务端开销 |
| 音频编码 | 手写 WAV header + PCM | 轻量无依赖，WAV 格式 mimo 原生支持 |
| UI 框架 | Vue 3 Composition API | 项目已有基础 |

### 后端

| 组件 | 选型 | 理由 |
|------|------|------|
| ASR 模型 | mimo-v2.5-asr | 题目指定 |
| API 客户端 | openai Python SDK | mimo 兼容 OpenAI 接口格式，官方示例即用此库 |
| Web 框架 | FastAPI | 项目已有基础 |

## 数据流

```
1. 页面加载
   └─ 请求麦克风权限 → 加载 Silero VAD 模型 → 开始持续监听

2. 语音检测循环
   └─ AudioWorklet 持续推送 PCM chunks
      └─ VAD 分析每帧
         ├─ 检测到语音 → 开始缓冲 PCM 数据
         ├─ 语音持续中 → 继续缓冲
         └─ 静音超过阈值(约2s) → 截断，进入处理

3. 音频处理
   └─ 缓冲的 PCM 数据
      ├─ 添加 WAV header（采样率、位深、声道数）
      └─ 转为 Blob

4. ASR 请求
   └─ POST /api/asr (FormData: audio file)
      └─ 后端读取文件 → base64 编码
         └─ 调用 mimo-v2.5-asr API
            └─ 返回识别文本

5. 结果展示
   └─ 前端接收文本 → 追加到识别历史列表
```

## 关键设计决策

### AudioWorklet vs MediaRecorder

**选择 AudioWorklet**。MediaRecorder 在 Chrome 中输出 webm/opus，mimo ASR 仅支持 wav/mp3。AudioWorklet 直接输出 PCM 原始数据，前端可自行封装 WAV，避免格式转换问题。

### VAD 方案

**选择 Silero VAD（@ricky0123/vad-web）**。基于 ONNX Runtime Web 的轻量 VAD 模型，运行在浏览器端。相比简单的能量阈值方案，对噪声环境更鲁棒。首次加载需下载约 1-2MB 模型文件，后续使用无额外开销。

### ASR 调用方式

**选择非流式调用**。当前阶段聚焦于将语音准确转为文字，非流式调用返回完整结果，逻辑更简单。流式 ASR 可作为后续优化。

### 静音截断阈值

默认 2 秒静音截断，以 VAD 配置参数暴露，方便调试。

## 目录结构

```
frontend/src/
├── components/
│   └── VoiceControl.vue          # 语音控制主组件
├── composables/
│   └── useVoiceCapture.ts        # 音频采集 + VAD 逻辑
├── utils/
│   └── wav-encoder.ts            # PCM → WAV 编码
└── App.vue                       # 入口

backend/
├── main.py                       # FastAPI 入口 + ASR 路由
└── requirements.txt              # 新增 openai 依赖
```
