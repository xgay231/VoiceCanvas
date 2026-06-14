## 1. Spec and Contract

- [x] 1.1 定义 `semantic-drawing-json` capability spec，覆盖成功绘图、澄清、无操作、不支持、解析失败等场景。
- [x] 1.2 明确 `/api/asr` 扩展响应契约，保留 `text` 与 `success`，新增结构化 `drawing` 字段。

## 2. Backend Implementation

- [x] 2.1 在后端封装 `mimo-v2.5-pro` 语义解析调用，复用现有 MIMO OpenAI-compatible client 配置。
- [x] 2.2 设计并接入绘图语义解析 Prompt，要求模型稳定输出 JSON。
- [x] 2.3 将 mimo-v2.5-pro 原始消息输出到控制台日志，便于调试。
- [x] 2.4 实现 JSON 解析与基础 schema 校验，失败时返回 `parse_error` 结构。
- [x] 2.5 将 `/api/asr` 流程串联为 ASR 转写 → 语义解析 → 扩展响应。

## 3. Tests and Verification

- [x] 3.1 为 Prompt 输出解析/校验逻辑添加后端单元测试，覆盖合法 JSON、非 JSON、字段缺失、未知动作。
- [x] 3.2 为 `/api/asr` 添加或更新测试，验证返回包含原始文本和结构化 `drawing` 字段。
- [x] 3.3 运行后端测试，必要时运行前端构建确认响应字段扩展不破坏现有前端。
