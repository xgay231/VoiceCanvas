---
change: add-fabric-canvas
design-doc: docs/superpowers/specs/2026-06-14-add-fabric-canvas-design.md
base-ref: 3ef4b9efd51d373bae81c6600b13a8db9b316f35
---

# Add Fabric Canvas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Vue 3 前端中加入一个独立的 Fabric.js 画布组件，显示 800x600 可交互画布、默认图形和 PNG 下载按钮，同时保留现有语音识别 UI。

**Architecture:** `DrawingCanvas.vue` 独立拥有 Fabric 生命周期、默认内容、导出行为和实例暴露；`App.vue` 只负责组合 `VoiceControl` 与 `DrawingCanvas`。依赖与构建能力在 `frontend/` 层补齐，避免修改后端、ASR、VAD、音频编码或现有语音流程。

**Tech Stack:** Vue 3 Composition API、`<script setup lang="ts">`、Fabric.js v5、Vite、Vitest、Tailwind CSS。

---

## 文件结构与职责

- 创建：`frontend/src/components/DrawingCanvas.vue`
  - 职责：渲染外层布局、下载按钮和 `<canvas>`；在 `onMounted` 初始化 `fabric.Canvas`；添加默认居中图形；在 `onUnmounted` 释放实例；通过 `defineExpose({ canvas })` 暴露 Fabric 实例。
- 修改：`frontend/src/App.vue`
  - 职责：导入并挂载 `DrawingCanvas`，保留现有 `VoiceControl`，提供简单页面布局。
- 修改：`frontend/package.json`
  - 职责：添加 Fabric 运行时依赖，以及 TypeScript、Tailwind/PostCSS/Autoprefixer 开发依赖。
- 修改：`frontend/package-lock.json`
  - 职责：由 `npm install` 自动更新锁文件，固定新增依赖版本。
- 创建：`frontend/tsconfig.json`
  - 职责：让 Vue SFC 的 `<script setup lang="ts">` 在 Vite 构建中有明确 TypeScript 配置。
- 创建：`frontend/tsconfig.node.json`
  - 职责：为 Vite 配置文件提供 Node 侧 TypeScript 配置引用。
- 创建：`frontend/src/env.d.ts`
  - 职责：声明 `.vue` 模块类型，避免 TypeScript 无法识别 SFC。
- 创建：`frontend/tailwind.config.js`
  - 职责：配置 Tailwind 扫描 `index.html` 与 `src` 下 Vue/JS/TS 文件。
- 创建：`frontend/postcss.config.js`
  - 职责：接入 `tailwindcss` 与 `autoprefixer`。
- 修改：`frontend/src/style.css`
  - 职责：加入 Tailwind 三个基础指令，保留现有全局 CSS。

## OpenSpec Tasks 映射

- `1.1`：Task 1 添加 `fabric@^5`。
- `1.2`：Task 2 添加 TypeScript 配置与 Vue SFC 类型声明。
- `1.3`：Task 3 添加 Tailwind/PostCSS 配置并接入全局 CSS。
- `2.1`、`2.2`、`2.3`、`2.4`、`2.5`、`2.6`：Task 4 创建 `DrawingCanvas.vue`。
- `3.1`：Task 5 在 `App.vue` 挂载画布且保留语音 UI。
- `3.2`：Task 6 运行测试和构建验证。

---

### Task 1: 添加 Fabric.js 依赖

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

- [x] **Step 1: 安装 Fabric v5**

Run:

```bash
cd frontend
npm install fabric@^5
```

Expected: `package.json` 的 `dependencies` 中出现 `"fabric": "^5.x.x"`，`package-lock.json` 同步更新。

- [x] **Step 2: 检查依赖声明**

确认 `frontend/package.json` 的依赖区域类似：

```json
"dependencies": {
  "@ricky0123/vad-web": "^0.0.30",
  "fabric": "^5.5.2",
  "vue": "^3.5.34"
}
```

Fabric 小版本以 `npm install` 实际写入为准，但必须保持主版本为 v5，以兼容：

```ts
import { fabric } from 'fabric'
```

- [x] **Step 3: 提交依赖变更**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore(frontend): add fabric canvas dependency"
```

---

### Task 2: 添加 TypeScript SFC 支持

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/src/env.d.ts`

- [x] **Step 1: 安装 TypeScript 开发依赖**

Run:

```bash
cd frontend
npm install -D typescript vue-tsc
```

Expected: `package.json` 的 `devDependencies` 中出现 `typescript` 和 `vue-tsc`，锁文件同步更新。

- [x] **Step 2: 创建 `frontend/tsconfig.json`**

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [x] **Step 3: 创建 `frontend/tsconfig.node.json`**

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.js"]
}
```

- [x] **Step 4: 创建 Vue SFC 类型声明**

Create `frontend/src/env.d.ts`:

```ts
declare module '*.vue' {
  import type { DefineComponent } from 'vue'

  const component: DefineComponent<object, object, unknown>
  export default component
}
```

- [x] **Step 5: 验证 TypeScript 配置不破坏现有 JS 入口**

Run:

```bash
cd frontend
npm run test
```

Expected: Vitest 执行完成，现有测试通过；如果没有测试文件，Vitest 应报告无测试或按项目当前行为结束，不应出现 TypeScript 配置解析错误。

- [x] **Step 6: 提交 TypeScript 支持**

```bash
git add frontend/package.json frontend/package-lock.json frontend/tsconfig.json frontend/tsconfig.node.json frontend/src/env.d.ts
git commit -m "chore(frontend): add typescript sfc support"
```

---

### Task 3: 添加 Tailwind CSS 支持

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Modify: `frontend/src/style.css`

- [x] **Step 1: 安装 Tailwind 相关开发依赖**

Run:

```bash
cd frontend
npm install -D tailwindcss postcss autoprefixer
```

Expected: `package.json` 的 `devDependencies` 中出现 `tailwindcss`、`postcss`、`autoprefixer`，锁文件同步更新。

- [x] **Step 2: 创建 `frontend/tailwind.config.js`**

Create `frontend/tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [x] **Step 3: 创建 `frontend/postcss.config.js`**

Create `frontend/postcss.config.js`:

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [x] **Step 4: 在全局 CSS 顶部接入 Tailwind**

Modify `frontend/src/style.css`，在文件最顶部加入：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

保留文件中已有的全局样式，不重写 `VoiceControl.vue` 的 scoped CSS。

- [x] **Step 5: 验证 PostCSS/Tailwind 能被 Vite 处理**

Run:

```bash
cd frontend
npm run build
```

Expected: Vite build 成功，不出现 Tailwind/PostCSS 插件加载错误。

- [x] **Step 6: 提交 Tailwind 配置**

```bash
git add frontend/package.json frontend/package-lock.json frontend/tailwind.config.js frontend/postcss.config.js frontend/src/style.css
git commit -m "chore(frontend): add tailwind styling support"
```

---

### Task 4: 创建 DrawingCanvas 组件

**Files:**
- Create: `frontend/src/components/DrawingCanvas.vue`

- [ ] **Step 1: 创建组件完整实现**

Create `frontend/src/components/DrawingCanvas.vue`:

```vue
<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { fabric } from 'fabric'

const CANVAS_WIDTH = 800
const CANVAS_HEIGHT = 600

const canvasElement = ref<HTMLCanvasElement | null>(null)
const canvas = ref<fabric.Canvas | null>(null)

function addDefaultShape(fabricCanvas: fabric.Canvas) {
  const rectangle = new fabric.Rect({
    width: 180,
    height: 120,
    fill: '#2563eb',
    stroke: '#1e40af',
    strokeWidth: 4,
    rx: 12,
    ry: 12,
    originX: 'center',
    originY: 'center',
    left: CANVAS_WIDTH / 2,
    top: CANVAS_HEIGHT / 2,
  })

  fabricCanvas.add(rectangle)
  fabricCanvas.setActiveObject(rectangle)
}

function downloadCanvas() {
  if (!canvas.value) {
    return
  }

  const dataUrl = canvas.value.toDataURL({
    format: 'png',
    multiplier: 1,
  })
  const link = document.createElement('a')
  link.href = dataUrl
  link.download = 'voicecanvas-drawing.png'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

onMounted(() => {
  if (!canvasElement.value) {
    return
  }

  const fabricCanvas = new fabric.Canvas(canvasElement.value, {
    width: CANVAS_WIDTH,
    height: CANVAS_HEIGHT,
    backgroundColor: '#f8fafc',
    preserveObjectStacking: true,
  })

  canvas.value = fabricCanvas
  addDefaultShape(fabricCanvas)
  fabricCanvas.renderAll()
})

onUnmounted(() => {
  if (!canvas.value) {
    return
  }

  canvas.value.dispose()
  canvas.value = null
})

defineExpose({ canvas })
</script>

<template>
  <section class="mx-auto w-full max-w-[880px] rounded-2xl bg-slate-100 p-4 shadow-sm">
    <div class="relative overflow-x-auto rounded-xl border border-slate-300 bg-white p-4 shadow-inner">
      <button
        type="button"
        class="absolute right-7 top-7 z-10 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
        :disabled="!canvas"
        @click="downloadCanvas"
      >
        下载
      </button>

      <canvas
        ref="canvasElement"
        class="block border border-slate-400 bg-slate-50 shadow-md"
        :width="CANVAS_WIDTH"
        :height="CANVAS_HEIGHT"
      />
    </div>
  </section>
</template>
```

- [ ] **Step 2: 对照设计要求检查组件行为**

确认组件满足：

```text
- 使用 <script setup lang="ts">
- 使用 ref、onMounted、onUnmounted
- 使用 import { fabric } from 'fabric'
- canvasElement 指向原生 <canvas>
- canvas 保存 fabric.Canvas | null
- defineExpose({ canvas }) 暴露实例
- Fabric 只在 onMounted 中初始化
- onUnmounted 中 dispose 并置空 canvas
- 默认图形 originX/originY 为 center，left/top 为 800/600 中心
- 下载按钮 disabled 状态绑定 !canvas
- 下载文件名为 voicecanvas-drawing.png
```

- [ ] **Step 3: 运行组件相关构建验证**

Run:

```bash
cd frontend
npm run build
```

Expected: build 成功；如果 Fabric 类型或 `toDataURL` 选项报错，优先保持 Fabric v5 导入方式，并只调整 TypeScript 类型写法，不改变组件职责。

- [ ] **Step 4: 提交画布组件**

```bash
git add frontend/src/components/DrawingCanvas.vue
git commit -m "feat(frontend): add fabric drawing canvas component"
```

---

### Task 5: 在 App 中挂载 DrawingCanvas

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 修改 `App.vue` 导入与模板**

Replace `frontend/src/App.vue` with:

```vue
<script setup>
import VoiceControl from './components/VoiceControl.vue'
import DrawingCanvas from './components/DrawingCanvas.vue'
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-4 py-8">
    <VoiceControl />
    <DrawingCanvas />
  </main>
</template>
```

- [ ] **Step 2: 确认未破坏语音 UI**

检查 `VoiceControl` 仍然被导入并在模板中渲染：

```vue
<VoiceControl />
<DrawingCanvas />
```

不要修改 `frontend/src/components/VoiceControl.vue`、`frontend/src/composables/useVoiceCapture.js`、`frontend/src/utils/wav-encoder.js` 或任何后端文件。

- [ ] **Step 3: 运行集成构建验证**

Run:

```bash
cd frontend
npm run build
```

Expected: build 成功，`App.vue` 能解析 `DrawingCanvas.vue`。

- [ ] **Step 4: 提交 App 集成**

```bash
git add frontend/src/App.vue
git commit -m "feat(frontend): mount drawing canvas in app"
```

---

### Task 6: 完整验证与手动检查

**Files:**
- Verify only: `frontend/src/components/DrawingCanvas.vue`
- Verify only: `frontend/src/App.vue`
- Verify only: `frontend/package.json`

- [ ] **Step 1: 运行前端测试**

Run:

```bash
cd frontend
npm run test
```

Expected: 现有 Vitest 测试通过；如果项目当前没有测试且 Vitest 以 no tests 失败，记录该现有测试覆盖状态，不为本 change 新增无关测试框架。

- [ ] **Step 2: 运行前端生产构建**

Run:

```bash
cd frontend
npm run build
```

Expected: Vite production build 成功，确认 Fabric、TypeScript SFC、Tailwind/PostCSS 都能被打包。

- [ ] **Step 3: 启动本地前端进行手动验证**

Run:

```bash
cd frontend
npm run dev
```

Expected: Vite dev server 启动并显示本地访问地址，通常是 `http://localhost:5173/`。

- [ ] **Step 4: 在浏览器完成手动验收**

打开 Vite 页面后确认：

```text
- 页面仍显示 VoiceCanvas 语音识别 UI
- 语音 UI 下方显示 800x600 画布
- 画布边框和浅色背景清晰可见
- 画布中央显示蓝色圆角矩形
- 矩形可以被选中并拖动
- 下载按钮位于画布 UI 右上角
- 点击下载生成 voicecanvas-drawing.png
- 下载的 PNG 只包含 Fabric 画布内容，不包含按钮或外层 wrapper
```

- [ ] **Step 5: 停止 dev server**

在运行 `npm run dev` 的终端按 `Ctrl+C`。

Expected: dev server 停止。

- [ ] **Step 6: 查看最终变更范围**

Run:

```bash
git status --short
git diff --stat HEAD~5..HEAD
```

Expected: 变更只集中在 `frontend/` 的依赖、配置、样式接入、`DrawingCanvas.vue` 和 `App.vue`。不应出现 `backend/`、VAD/ONNX 资源或音频编码文件变更。

- [ ] **Step 7: 提交验证记录（如有补充修正）**

如果验证过程中只运行命令且没有文件变更，不需要提交。如果为修复验证失败修改了文件，提交相关文件：

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/components/DrawingCanvas.vue frontend/src/App.vue frontend/src/style.css frontend/tailwind.config.js frontend/postcss.config.js frontend/tsconfig.json frontend/tsconfig.node.json frontend/src/env.d.ts
git commit -m "fix(frontend): stabilize fabric canvas build"
```

---

## 自检结果

- Spec coverage: 设计文档中的依赖、TypeScript SFC、Tailwind、800x600 可见画布、默认可交互形状、下载按钮、实例暴露、卸载清理、App 集成、构建/测试/手动验证均映射到 Task 1-6。
- Placeholder scan: 计划中没有 `TBD`、`TODO`、`implement later` 或未展开的“类似上一任务”。
- Type consistency: 计划统一使用 `canvasElement`、`canvas`、`CANVAS_WIDTH`、`CANVAS_HEIGHT`、`downloadCanvas`、`addDefaultShape`，Fabric 实例类型统一为 `fabric.Canvas | null`。
- Scope guard: 计划不修改后端、ASR、VAD/ONNX 资源、WAV 编码或语音识别逻辑；不加入绘图工具栏、持久化、撤销/重做、缩放或语音控制画布。

## 执行交接

Plan complete and saved to `docs/superpowers/plans/2026-06-14-add-fabric-canvas.md`. Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
