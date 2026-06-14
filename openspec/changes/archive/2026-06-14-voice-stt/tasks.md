## Tasks

- [x] 1. 后端：创建 ASR API 路由（`/api/asr`），接收音频文件，base64 编码调用 mimo-v2.5-asr，返回识别文本
- [x] 2. 前端：安装依赖（@ricky0123/vad-web），实现 WAV 编码工具（PCM + WAV header → Blob）
- [x] 3. 前端：实现 useVoiceCapture composable（MicVAD 一体化：音频采集 + VAD 检测 + WAV 编码 + 自动重试）
- [x] 4. 前端：实现 VoiceControl 组件（语音状态显示、识别结果列表、调用后端 ASR）
- [x] 5. 集成测试：端到端验证（麦克风采集 → VAD 截断 → ASR 识别 → 文本展示）
