# VoiceCanvas

> 语音驱动画布绘图 — 说出指令，即可在画布上创建图形。

**VoiceCanvas** 是一款语音驱动绘图应用。你只需自然说话（例如"在中间画一个红色的圆"），语音在浏览器端被采集，经 AI 语音识别模型转写为文字，再被解析为结构化的绘图指令，最终在交互式画布上实时渲染。

## Demo 演示

[在 Bilibili 上观看演示视频](https://www.bilibili.com/video/BV1pDJA6eEQN)

## 工作原理

```
浏览器 (Vue 3)                    后端 (FastAPI)                   AI 服务
────────────                       ──────────────                  ───────────
MicVAD + Silero VAD               POST /api/asr                       ASR
(检测语音段落)            ──WAV──▶   base64 编码  ──────────────▶  (语音转文字)
     │                                    │
     │                           POST /api/interpret-drawing          LLM
     │                           (文本 → 绘图 JSON)  ───────────▶  (语义解析)
     │                                    │
Fabric.js 画布  ◀────── 绘图 JSON ────────┘
(渲染图形)
```

1. **语音采集** — 基于浏览器的语音活动检测（VAD），使用 Silero 模型通过 ONNX Runtime WASM 运行。语音段落被编码为 16kHz 单声道 16 位 WAV 格式。
2. **语音识别** — WAV 音频发送至后端，后端调用 ASR 模型（mimo-v2.5-asr）将语音转写为文字。
3. **语义解析** — 转写文本发送至大语言模型（`mimo-v2.5-pro`），解析为结构化的绘图 JSON（包含图形类型、位置、颜色、尺寸等）。
4. **画布渲染** — 绘图指令在 Fabric.js 画布上执行，支持矩形、圆形、文字和线条。

## 项目结构

```
VoiceCanvas/
├── frontend/                  # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── App.vue                        # 根组件
│   │   ├── components/
│   │   │   ├── VoiceControl.vue           # 语音采集 UI 与识别结果展示
│   │   │   └── DrawingCanvas.vue          # Fabric.js 画布与绘图指令执行
│   │   ├── composables/
│   │   │   └── useVoiceCapture.js         # MicVAD 生命周期管理与 ASR 重试逻辑
│   │   ├── api/
│   │   │   └── drawingInterpreter.js      # 绘图解析 API 客户端
│   │   └── utils/
│   │       └── wav-encoder.js             # PCM 转 WAV 编码器
│   ├── vite.config.js
│   └── package.json
├── backend/                   # FastAPI 后端
│   ├── main.py                            # API 服务（ASR + 绘图解析接口）
│   ├── drawing_interpreter.py             # 语义解析与校验
│   ├── tests/
│   │   ├── test_asr.py
│   │   ├── test_drawing_interpreter.py
│   │   └── test_interpret_drawing_endpoint.py
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## 快速开始

### 环境要求

- **Node.js** ≥ 18（前端）
- **Python** ≥ 3.10（后端）

### 后端配置

```bash
cd backend

# 创建并激活虚拟环境
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env — 填入你的 MIMO_API_KEY 和 MIMO_BASE_URL

# 启动服务
uvicorn main:app --reload
```

API 服务将运行在 `http://127.0.0.1:8000`。

### 前端配置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

在浏览器中打开 `http://localhost:5173`。Vite 开发服务器会将 `/api` 请求代理到后端的 8000 端口。

### 使用方式

1. 点击 **"Start Listening"** 并授权麦克风权限。
2. 说出绘图指令 — 例如：_"在中间画一个蓝色的圆"_ 或 _"在上方用红色写'你好'"_。
3. 应用将自动转写你的语音、解析意图，并在画布上渲染结果。
4. 点击 **下载** 按钮将画布保存为 PNG 图片。

## 依赖说明

### 前端 — 运行时依赖

| 库                                                         | 版本    | 用途                                                  |
| ---------------------------------------------------------- | ------- | ----------------------------------------------------- |
| [Vue 3](https://vuejs.org/)                                | ^3.5    | 响应式 UI 框架                                        |
| [@ricky0123/vad-web](https://github.com/ricky0123/vad-web) | ^0.0.30 | 浏览器端语音活动检测（Silero VAD，基于 ONNX Runtime） |
| [Fabric.js](http://fabricjs.com/)                          | ^5.5    | 交互式画布绘图与渲染                                  |

### 前端 — 开发依赖

| 库                                                                                        | 用途                    |
| ----------------------------------------------------------------------------------------- | ----------------------- |
| [Vite](https://vite.dev/)                                                                 | 构建工具与开发服务器    |
| [Vitest](https://vitest.dev/)                                                             | 单元测试框架            |
| [Tailwind CSS](https://tailwindcss.com/) v4                                               | 实用优先的 CSS 框架     |
| [TypeScript](https://www.typescriptlang.org/)                                             | 类型安全的 JavaScript   |
| [vue-tsc](https://github.com/vuejs/language-tools)                                        | Vue TypeScript 类型检查 |
| [PostCSS](https://postcss.org/) + [Autoprefixer](https://github.com/postcss/autoprefixer) | CSS 处理                |

### 后端依赖

| 库                                                             | 版本    | 用途                                |
| -------------------------------------------------------------- | ------- | ----------------------------------- |
| [FastAPI](https://fastapi.tiangolo.com/)                       | 0.136   | Web 框架                            |
| [Uvicorn](https://www.uvicorn.org/)                            | 0.49    | ASGI 服务器                         |
| [OpenAI Python SDK](https://github.com/openai/openai-python)   | ≥ 1.0   | OpenAI 兼容客户端                   |
| [python-multipart](https://github.com/Kludex/python-multipart) | ≥ 0.0.6 | 文件上传支持（multipart/form-data） |
| [pytest](https://pytest.org/)                                  | ≥ 7.0   | 测试框架                            |
| [httpx](https://www.python-httpx.org/)                         | ≥ 0.24  | HTTP 客户端（测试辅助）             |

## 原创功能部分

以下模块为 VoiceCanvas 的**原创实现**（非第三方库包装）：

### 1. WAV 编码器 ([frontend/src/utils/wav-encoder.js](frontend/src/utils/wav-encoder.js))

自研、零依赖的 WAV 文件编码器。将浏览器 VAD 引擎输出的 Float32Array PCM 采样数据转换为符合标准的 16kHz 单声道 16 位 PCM WAV Blob。自行实现 RIFF 文件头构建、采样格式转换（float → int16）以及基于 DataView 的字节级操作。

### 2. 绘图语义解析器 ([backend/drawing_interpreter.py](backend/drawing_interpreter.py))

将自然语言文本转换为结构化、经校验的 JSON 绘图指令的语义解析管线，是整个项目的核心"智能"层：

- **提示词工程** — 详细的系统提示词定义了输出 schema（`draw` / `clarification` / `no_op` / `unsupported`）、支持的图形类型、动作类型以及语义化的位置/尺寸预设。
- **JSON 提取与校验** — 解析 LLM 输出（处理 markdown 代码块包裹）、校验必填字段、强制枚举值、规范化别名（如 `type` → `shape`）。
- **错误信封机制** — 区分解析错误、语义错误和不支持的操作，向用户返回相应的错误信息。

### 3. 语音采集组合式函数 ([frontend/src/composables/useVoiceCapture.js](frontend/src/composables/useVoiceCapture.js))

自定义 Vue 3 组合式函数，编排完整的语音采集生命周期：

- 管理 MicVAD 实例的创建及 ONNX WASM 资源加载。
- 协调麦克风权限请求、音频流的暂停/恢复以及资源释放。
- 实现带指数退避的 ASR 请求重试逻辑（1s → 2s → 4s）。
- 追踪状态机流转（`idle` → `listening` → `speaking` → `processing`）。

### 4. 语音驱动的绘图画布 ([frontend/src/components/DrawingCanvas.vue](frontend/src/components/DrawingCanvas.vue))

将 Fabric.js 与语音指令执行相结合：

- 将结构化的绘图 JSON 转换为 Fabric.js 图形对象（矩形、圆形、文字、线条）。
- 为语义预设提供合理的默认值，并进行参数校验。
- 暴露 `executeDrawing()` 方法，供父组件以编程方式控制。

### 5. 端到端管线架构

从浏览器 VAD → WAV 编码 → ASR 转写 → 语义解析 → 画布渲染的完整端到端语音绘图管线，是本项目的独特集成设计。各层之间的组件通信、事件流以及错误处理均为原创架构。

## API 接口

| 接口                     | 方法 | 说明                                            |
| ------------------------ | ---- | ----------------------------------------------- |
| `/`                      | GET  | 根路径 — 返回 API 状态                          |
| `/health`                | GET  | 健康检查 — 返回 `{"status": "ok"}`              |
| `/api/asr`               | POST | 上传 WAV 音频 → 返回 `{text, success, drawing}` |
| `/api/interpret-drawing` | POST | 提交文本 → 返回 `{success, drawing}`            |

### 支持的绘图指令

| 图形 | 语音指令示例                                       |
| ---- | -------------------------------------------------- |
| 矩形 | "画一个蓝色的长方形"、"在中间加一个大的红色正方形" |
| 圆形 | "画一个圆"、"在左上角放一个小的绿色圆"             |
| 文字 | "用红色写'你好世界'"、"添加文字'欢迎'"             |
| 线条 | "画一条线"、"加一条粗的橙色线"                     |

## 运行测试

### 后端

```bash
cd backend
pytest tests/ -v
```

### 前端

```bash
cd frontend
npm run test
```

## 开源协议

MIT
