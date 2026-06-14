---
change: execute-drawing-instructions
design-doc: docs/superpowers/specs/2026-06-14-execute-drawing-instructions-design.md
base-ref: f5c292af1fd910ec1ce1d26c43f8834c686dbf3b
---

# Execute Drawing Instructions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将语音识别 transcript 通过 `/api/interpret-drawing` 转换为 drawing envelope，并在 Fabric.js 画布上安全执行基础创建动作。

**Architecture:** `VoiceControl` 保持语音状态与识别历史展示，并在新 transcript 出现后调用独立绘图解析接口。`App.vue` 作为轻量协调层接收 drawing envelope 并调用 `DrawingCanvas` 暴露的受控执行入口。`DrawingCanvas` 内部只执行白名单内的 `create` rectangle/circle/text/line，并对非支持动作返回可展示反馈。

**Tech Stack:** Vue 3 `<script setup>`、Fabric.js 5、Vitest + Vue Test Utils、FastAPI + pytest。

---

## File Structure

- Modify: `backend/tests/test_interpret_drawing_endpoint.py`
  - Add focused endpoint assertions that `/api/interpret-drawing` returns the full drawing envelope fields and displayable non-draw messages.
- Create: `frontend/src/api/drawingInterpreter.js`
  - Owns the standalone fetch call to `/api/interpret-drawing` so `VoiceControl` does not inline API details.
- Create: `frontend/src/api/__tests__/drawingInterpreter.test.js`
  - Tests request body, success response parsing, and HTTP/network failure behavior.
- Modify: `frontend/src/components/DrawingCanvas.vue`
  - Adds `executeDrawing(drawing)` and internal shape mapping helpers for rectangle, circle, text, and line.
- Modify: `frontend/src/components/__tests__/DrawingCanvas.test.ts`
  - Extends Fabric mocks and verifies supported actions, unsupported actions, and non-draw/no-op canvas safety.
- Modify: `frontend/src/components/VoiceControl.vue`
  - Calls `interpretDrawingText` for new transcripts, emits draw envelopes, and displays drawing interpretation messages.
- Create: `frontend/src/components/__tests__/VoiceControl.test.js`
  - Mocks voice capture and drawing API to verify transcript submission, draw emission, and non-draw message display.
- Modify: `frontend/src/App.vue`
  - Holds the canvas ref and wires `VoiceControl` drawing events to `DrawingCanvas.executeDrawing`.
- Create: `frontend/src/App.test.js`
  - Verifies App forwards emitted draw envelopes to the canvas entrypoint.
- Modify: `openspec/changes/execute-drawing-instructions/tasks.md`
  - Check off OpenSpec tasks as implementation/verification tasks complete.

## Task 1: Backend Endpoint Contract Coverage

**Files:**
- Modify: `backend/tests/test_interpret_drawing_endpoint.py:24-112`

- [x] **Step 1: Add failing endpoint contract assertions**

Add this test to `TestInterpretDrawingEndpoint` after `test_returns_draw_envelope`:

```python
    def test_returns_complete_drawing_contract_for_frontend_execution(self, client):
        raw = json.dumps({
            "version": "1.0",
            "type": "draw",
            "actions": [
                {"action": "create", "shape": "rectangle", "params": {"fill": "#2563eb"}}
            ],
            "requires_clarification": False,
            "message": None,
        })
        with patch("main.client") as mock_client:
            mock_client.chat.completions.create.return_value = _mock_completion(raw)
            response = client.post("/api/interpret-drawing", json={"text": "画一个蓝色矩形"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert set(data["drawing"].keys()) == {
            "version",
            "type",
            "actions",
            "requires_clarification",
            "message",
        }
        assert data["drawing"]["version"] == "1.0"
        assert data["drawing"]["type"] == "draw"
        assert data["drawing"]["actions"][0]["shape"] == "rectangle"
        assert data["drawing"]["requires_clarification"] is False
        assert data["drawing"]["message"] is None
```

Add this assertion to existing non-draw tests:

```python
        assert data["drawing"]["message"]
```

Apply it in `test_returns_clarification`, `test_returns_noop`, `test_returns_unsupported`, `test_returns_parse_error_on_invalid_json`, and `test_returns_semantic_error_on_api_failure`.

- [x] **Step 2: Run backend endpoint tests**

Run from `backend/`:

```bash
.venv/Scripts/python -m pytest tests/test_interpret_drawing_endpoint.py -v
```

Expected: PASS. If this fails, inspect whether the current endpoint already violates the frontend contract before changing production code.

- [x] **Step 3: Commit backend contract coverage**

```bash
git add backend/tests/test_interpret_drawing_endpoint.py
git commit -m "test(backend): cover drawing interpretation endpoint contract"
```

- [x] **Step 4: Mark OpenSpec backend task complete if tests pass**

Change the first checkbox in `openspec/changes/execute-drawing-instructions/tasks.md` from:

```markdown
- [ ] Inspect current backend standalone drawing interpretation endpoint and align its response contract with frontend execution needs.
```

to:

```markdown
- [x] Inspect current backend standalone drawing interpretation endpoint and align its response contract with frontend execution needs.
```

Then amend with a new commit, not amend the previous one:

```bash
git add openspec/changes/execute-drawing-instructions/tasks.md
git commit -m "chore(openspec): mark drawing endpoint contract checked"
```

## Task 2: Frontend Drawing Interpretation API Helper

**Files:**
- Create: `frontend/src/api/drawingInterpreter.js`
- Create: `frontend/src/api/__tests__/drawingInterpreter.test.js`

- [x] **Step 1: Write failing API helper tests**

Create `frontend/src/api/__tests__/drawingInterpreter.test.js`:

```js
import { afterEach, describe, expect, it, vi } from 'vitest'
import { interpretDrawingText } from '../drawingInterpreter.js'

describe('interpretDrawingText', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('posts transcript text to the standalone drawing endpoint', async () => {
    const drawing = {
      version: '1.0',
      type: 'draw',
      actions: [],
      requires_clarification: false,
      message: null,
    }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, drawing }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await interpretDrawingText('画一个蓝色圆形')

    expect(fetchMock).toHaveBeenCalledWith('/api/interpret-drawing', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: '画一个蓝色圆形' }),
    })
    expect(result).toEqual(drawing)
  })

  it('throws when the endpoint returns no drawing envelope', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: false }),
    }))

    await expect(interpretDrawingText('画一个圆')).rejects.toThrow('Drawing interpretation failed')
  })

  it('throws when the endpoint request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    }))

    await expect(interpretDrawingText('画一个圆')).rejects.toThrow('Drawing interpretation request failed')
  })
})
```

- [x] **Step 2: Run API helper tests to verify failure**

Run from `frontend/`:

```bash
npm run test -- src/api/__tests__/drawingInterpreter.test.js
```

Expected: FAIL with module not found for `../drawingInterpreter.js`.

- [x] **Step 3: Implement API helper**

Create `frontend/src/api/drawingInterpreter.js`:

```js
export async function interpretDrawingText(text) {
  const response = await fetch('/api/interpret-drawing', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })

  if (!response.ok) {
    throw new Error(`Drawing interpretation request failed: ${response.status}`)
  }

  const data = await response.json()

  if (!data.success || !data.drawing) {
    throw new Error('Drawing interpretation failed')
  }

  return data.drawing
}
```

- [x] **Step 4: Run API helper tests to verify pass**

Run from `frontend/`:

```bash
npm run test -- src/api/__tests__/drawingInterpreter.test.js
```

Expected: PASS.

- [x] **Step 5: Commit API helper**

```bash
git add frontend/src/api/drawingInterpreter.js frontend/src/api/__tests__/drawingInterpreter.test.js
git commit -m "feat(frontend): add drawing interpretation API helper"
```

## Task 3: DrawingCanvas Execution Entrypoint

**Files:**
- Modify: `frontend/src/components/DrawingCanvas.vue:1-100`
- Modify: `frontend/src/components/__tests__/DrawingCanvas.test.ts:1-83`

- [x] **Step 1: Extend Fabric mocks and write failing canvas execution tests**

Replace the Fabric mock setup in `frontend/src/components/__tests__/DrawingCanvas.test.ts` with constructors that expose their `opts`:

```ts
const mockAdd = vi.fn()
const mockSetActiveObject = vi.fn()
const mockRenderAll = vi.fn()
const mockDispose = vi.fn()

class MockRect {
  constructor(public opts: unknown) {}
}

class MockCircle {
  constructor(public opts: unknown) {}
}

class MockText {
  constructor(public text: string, public opts: unknown) {}
}

class MockLine {
  constructor(public points: number[], public opts: unknown) {}
}

vi.mock('fabric', () => {
  const mockWrapper = document.createElement('div')
  return {
    fabric: {
      Canvas: class MockCanvas {
        add = mockAdd
        setActiveObject = mockSetActiveObject
        renderAll = mockRenderAll
        dispose = mockDispose
        wrapperEl = mockWrapper
      },
      Rect: MockRect,
      Circle: MockCircle,
      Text: MockText,
      Line: MockLine,
    },
  }
})
```

Add these tests to the `describe('DrawingCanvas')` block:

```ts
  it('executes supported create actions and renders the canvas', () => {
    const wrapper = mount(DrawingCanvas)
    vi.clearAllMocks()

    const result = wrapper.vm.executeDrawing({
      version: '1.0',
      type: 'draw',
      actions: [
        { action: 'create', shape: 'rectangle', params: { x: 100, y: 120, width: 80, height: 40, fill: '#2563eb' } },
        { action: 'create', shape: 'circle', params: { x: 200, y: 220, radius: 30, fill: 'blue' } },
        { action: 'create', shape: 'text', params: { x: 300, y: 320, text: '你好', fontSize: 24 } },
        { action: 'create', shape: 'line', params: { x1: 10, y1: 20, x2: 110, y2: 120, stroke: '#111827' } },
      ],
    })

    expect(result).toEqual({ executed: 4, skipped: 0, message: null })
    expect(mockAdd).toHaveBeenCalledTimes(4)
    expect(mockSetActiveObject).toHaveBeenCalledTimes(4)
    expect(mockRenderAll).toHaveBeenCalledTimes(1)
  })

  it('skips unsupported actions without throwing', () => {
    const wrapper = mount(DrawingCanvas)
    vi.clearAllMocks()

    const result = wrapper.vm.executeDrawing({
      version: '1.0',
      type: 'draw',
      actions: [
        { action: 'update', shape: 'rectangle', params: {} },
        { action: 'create', shape: 'triangle', params: {} },
      ],
    })

    expect(result).toEqual({ executed: 0, skipped: 2, message: '部分绘图指令暂不支持，已跳过。' })
    expect(mockAdd).not.toHaveBeenCalled()
    expect(mockRenderAll).not.toHaveBeenCalled()
  })

  it('does not execute non-draw envelopes', () => {
    const wrapper = mount(DrawingCanvas)
    vi.clearAllMocks()

    const result = wrapper.vm.executeDrawing({
      version: '1.0',
      type: 'no_op',
      actions: [{ action: 'create', shape: 'circle', params: {} }],
      message: '不是绘图指令',
    })

    expect(result).toEqual({ executed: 0, skipped: 1, message: '不是绘图指令' })
    expect(mockAdd).not.toHaveBeenCalled()
  })
```

- [x] **Step 2: Run canvas tests to verify failure**

Run from `frontend/`:

```bash
npm run test -- src/components/__tests__/DrawingCanvas.test.ts
```

Expected: FAIL because `executeDrawing` is not exposed.

- [x] **Step 3: Implement execution entrypoint in DrawingCanvas**

In `frontend/src/components/DrawingCanvas.vue`, add these helpers inside `<script setup lang="ts">` before `onMounted`:

```ts
type DrawingAction = {
  action?: string
  shape?: string
  type?: string
  params?: Record<string, unknown>
}

type DrawingEnvelope = {
  type?: string
  actions?: DrawingAction[]
  message?: string | null
}

type ExecutionResult = {
  executed: number
  skipped: number
  message: string | null
}

const DEFAULT_FILL = '#2563eb'
const DEFAULT_STROKE = '#1e40af'

function numberParam(params: Record<string, unknown>, key: string, fallback: number) {
  const value = params[key]
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function stringParam(params: Record<string, unknown>, key: string, fallback: string) {
  const value = params[key]
  return typeof value === 'string' && value.trim() ? value : fallback
}

function makeRectangle(params: Record<string, unknown>) {
  return new fabric.Rect({
    width: numberParam(params, 'width', 120),
    height: numberParam(params, 'height', 80),
    fill: stringParam(params, 'fill', DEFAULT_FILL),
    stroke: stringParam(params, 'stroke', DEFAULT_STROKE),
    strokeWidth: numberParam(params, 'strokeWidth', 2),
    originX: 'center',
    originY: 'center',
    left: numberParam(params, 'x', CANVAS_WIDTH / 2),
    top: numberParam(params, 'y', CANVAS_HEIGHT / 2),
  })
}

function makeCircle(params: Record<string, unknown>) {
  return new fabric.Circle({
    radius: numberParam(params, 'radius', 50),
    fill: stringParam(params, 'fill', DEFAULT_FILL),
    stroke: stringParam(params, 'stroke', DEFAULT_STROKE),
    strokeWidth: numberParam(params, 'strokeWidth', 2),
    originX: 'center',
    originY: 'center',
    left: numberParam(params, 'x', CANVAS_WIDTH / 2),
    top: numberParam(params, 'y', CANVAS_HEIGHT / 2),
  })
}

function makeText(params: Record<string, unknown>) {
  return new fabric.Text(stringParam(params, 'text', 'Text'), {
    fill: stringParam(params, 'fill', '#111827'),
    fontSize: numberParam(params, 'fontSize', 32),
    originX: 'center',
    originY: 'center',
    left: numberParam(params, 'x', CANVAS_WIDTH / 2),
    top: numberParam(params, 'y', CANVAS_HEIGHT / 2),
  })
}

function makeLine(params: Record<string, unknown>) {
  return new fabric.Line([
    numberParam(params, 'x1', CANVAS_WIDTH / 2 - 80),
    numberParam(params, 'y1', CANVAS_HEIGHT / 2),
    numberParam(params, 'x2', CANVAS_WIDTH / 2 + 80),
    numberParam(params, 'y2', CANVAS_HEIGHT / 2),
  ], {
    stroke: stringParam(params, 'stroke', DEFAULT_STROKE),
    strokeWidth: numberParam(params, 'strokeWidth', 4),
  })
}

function createFabricObject(action: DrawingAction) {
  if (action.action !== 'create') {
    return null
  }

  const shape = action.shape || action.type
  const params = action.params || {}

  if (shape === 'rectangle') {
    return makeRectangle(params)
  }
  if (shape === 'circle') {
    return makeCircle(params)
  }
  if (shape === 'text') {
    return makeText(params)
  }
  if (shape === 'line') {
    return makeLine(params)
  }

  return null
}

function executeDrawing(drawing: DrawingEnvelope): ExecutionResult {
  const actions = Array.isArray(drawing.actions) ? drawing.actions : []

  if (drawing.type !== 'draw') {
    return {
      executed: 0,
      skipped: actions.length,
      message: drawing.message || null,
    }
  }

  if (!canvas.value) {
    return { executed: 0, skipped: actions.length, message: '画布尚未准备好。' }
  }

  let executed = 0
  let skipped = 0

  for (const action of actions) {
    const object = createFabricObject(action)
    if (!object) {
      skipped += 1
      continue
    }

    canvas.value.add(object)
    canvas.value.setActiveObject(object)
    executed += 1
  }

  if (executed > 0) {
    canvas.value.renderAll()
  }

  return {
    executed,
    skipped,
    message: skipped > 0 ? '部分绘图指令暂不支持，已跳过。' : null,
  }
}
```

Update `defineExpose` at the bottom of the script from:

```ts
defineExpose({ canvas })
```

to:

```ts
defineExpose({ canvas, executeDrawing })
```

- [x] **Step 4: Run canvas tests to verify pass**

Run from `frontend/`:

```bash
npm run test -- src/components/__tests__/DrawingCanvas.test.ts
```

Expected: PASS.

- [x] **Step 5: Commit canvas execution entrypoint**

```bash
git add frontend/src/components/DrawingCanvas.vue frontend/src/components/__tests__/DrawingCanvas.test.ts
git commit -m "feat(frontend): execute basic drawing actions on canvas"
```

- [x] **Step 6: Mark OpenSpec canvas task complete**

Change this checkbox in `openspec/changes/execute-drawing-instructions/tasks.md`:

```markdown
- [ ] Add a controlled DrawingCanvas execution entrypoint that maps supported `create` actions to Fabric.js rectangle, circle, text, and line objects.
```

to:

```markdown
- [x] Add a controlled DrawingCanvas execution entrypoint that maps supported `create` actions to Fabric.js rectangle, circle, text, and line objects.
```

Commit:

```bash
git add openspec/changes/execute-drawing-instructions/tasks.md
git commit -m "chore(openspec): mark canvas execution task complete"
```

## Task 4: VoiceControl Interpretation Flow

**Files:**
- Modify: `frontend/src/components/VoiceControl.vue:1-170`
- Create: `frontend/src/components/__tests__/VoiceControl.test.js`

- [x] **Step 1: Write failing VoiceControl tests**

Create `frontend/src/components/__tests__/VoiceControl.test.js`:

```js
// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'

const mockResults = ref([])
const mockStatus = ref('idle')
const mockError = ref(null)
const mockStart = vi.fn()
const mockStop = vi.fn()
const mockInterpretDrawingText = vi.fn()

vi.mock('../../composables/useVoiceCapture.js', () => ({
  useVoiceCapture: () => ({
    status: mockStatus,
    results: mockResults,
    error: mockError,
    start: mockStart,
    stop: mockStop,
  }),
}))

vi.mock('../../api/drawingInterpreter.js', () => ({
  interpretDrawingText: (...args) => mockInterpretDrawingText(...args),
}))

import VoiceControl from '../VoiceControl.vue'

describe('VoiceControl drawing interpretation', () => {
  beforeEach(() => {
    mockResults.value = []
    mockStatus.value = 'idle'
    mockError.value = null
    mockStart.mockReset()
    mockStop.mockReset()
    mockInterpretDrawingText.mockReset()
  })

  it('submits new transcript text to the drawing interpretation endpoint', async () => {
    mockInterpretDrawingText.mockResolvedValue({
      version: '1.0',
      type: 'draw',
      actions: [],
      requires_clarification: false,
      message: null,
    })
    mount(VoiceControl)

    mockResults.value = [{ text: '画一个圆', timestamp: 1 }]
    await flushPromises()

    expect(mockInterpretDrawingText).toHaveBeenCalledWith('画一个圆')
  })

  it('emits draw envelopes for App coordination', async () => {
    const drawing = {
      version: '1.0',
      type: 'draw',
      actions: [{ action: 'create', shape: 'circle', params: {} }],
      requires_clarification: false,
      message: null,
    }
    mockInterpretDrawingText.mockResolvedValue(drawing)
    const wrapper = mount(VoiceControl)

    mockResults.value = [{ text: '画一个圆', timestamp: 1 }]
    await flushPromises()

    expect(wrapper.emitted('drawing')).toEqual([[drawing]])
  })

  it('shows non-draw drawing messages without emitting draw envelopes', async () => {
    mockInterpretDrawingText.mockResolvedValue({
      version: '1.0',
      type: 'unsupported',
      actions: [],
      requires_clarification: false,
      message: '暂不支持旋转操作',
    })
    const wrapper = mount(VoiceControl)

    mockResults.value = [{ text: '旋转图形', timestamp: 1 }]
    await flushPromises()

    expect(wrapper.text()).toContain('暂不支持旋转操作')
    expect(wrapper.emitted('drawing')).toBeUndefined()
  })
})
```

- [x] **Step 2: Run VoiceControl tests to verify failure**

Run from `frontend/`:

```bash
npm run test -- src/components/__tests__/VoiceControl.test.js
```

Expected: FAIL because `VoiceControl` does not call `interpretDrawingText` or emit `drawing`.

- [x] **Step 3: Implement VoiceControl interpretation flow**

Update `frontend/src/components/VoiceControl.vue` script to import the helper, define an emit, track the last processed result, and display messages:

```vue
<script setup>
import { ref, watch, nextTick } from 'vue'
import { useVoiceCapture } from '../composables/useVoiceCapture.js'
import { interpretDrawingText } from '../api/drawingInterpreter.js'

const emit = defineEmits(['drawing'])
const { status, results, error, start, stop } = useVoiceCapture()

const resultsContainer = ref(null)
const drawingMessage = ref(null)
let lastInterpretedTimestamp = null

function toggle() {
  if (status.value === 'idle' || status.value === 'error') {
    start()
  } else {
    stop()
  }
}

async function interpretLatestResult() {
  const latest = results.value[results.value.length - 1]
  if (!latest || latest.timestamp === lastInterpretedTimestamp) {
    return
  }

  lastInterpretedTimestamp = latest.timestamp
  drawingMessage.value = null

  try {
    const drawing = await interpretDrawingText(latest.text)
    if (drawing.type === 'draw') {
      emit('drawing', drawing)
      if (drawing.message) {
        drawingMessage.value = drawing.message
      }
      return
    }

    drawingMessage.value = drawing.message || '这句话没有生成可执行的绘图指令。'
  } catch (err) {
    drawingMessage.value = err.message || '绘图指令解析失败。'
  }
}

watch(
  () => results.value.length,
  async () => {
    await nextTick()
    if (resultsContainer.value) {
      resultsContainer.value.scrollTop = resultsContainer.value.scrollHeight
    }
    await interpretLatestResult()
  },
)
</script>
```

Add the message display below the existing ASR error message in the template:

```vue
    <p v-if="drawingMessage" class="drawing-msg">{{ drawingMessage }}</p>
```

Add this style near `.error-msg`:

```css
.drawing-msg {
  color: #1d4ed8;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
```

- [x] **Step 4: Run VoiceControl tests to verify pass**

Run from `frontend/`:

```bash
npm run test -- src/components/__tests__/VoiceControl.test.js
```

Expected: PASS.

- [x] **Step 5: Commit VoiceControl flow**

```bash
git add frontend/src/components/VoiceControl.vue frontend/src/components/__tests__/VoiceControl.test.js
git commit -m "feat(frontend): interpret recognized text for drawing"
```

- [x] **Step 6: Mark OpenSpec frontend API task complete**

Change this checkbox in `openspec/changes/execute-drawing-instructions/tasks.md`:

```markdown
- [ ] Add or update frontend API flow so recognized transcript text is submitted to the standalone drawing interpretation endpoint.
```

to:

```markdown
- [x] Add or update frontend API flow so recognized transcript text is submitted to the standalone drawing interpretation endpoint.
```

Commit:

```bash
git add openspec/changes/execute-drawing-instructions/tasks.md
git commit -m "chore(openspec): mark drawing interpretation flow complete"
```

## Task 5: App Coordination Wiring

**Files:**
- Modify: `frontend/src/App.vue:1-11`
- Create: `frontend/src/App.test.js`

- [x] **Step 1: Write failing App coordination test**

Create `frontend/src/App.test.js`:

```js
// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import App from './App.vue'

describe('App drawing coordination', () => {
  it('passes draw envelopes from VoiceControl to DrawingCanvas', async () => {
    const drawing = {
      version: '1.0',
      type: 'draw',
      actions: [{ action: 'create', shape: 'circle', params: {} }],
      requires_clarification: false,
      message: null,
    }

    const wrapper = mount(App, {
      global: {
        stubs: {
          VoiceControl: {
            emits: ['drawing'],
            template: '<button class="emit-drawing" @click="$emit(\'drawing\', drawing)">emit</button>',
            data: () => ({ drawing }),
          },
          DrawingCanvas: {
            template: '<div class="drawing-canvas"></div>',
            methods: {
              executeDrawing(drawingEnvelope) {
                this.$emit('executed', drawingEnvelope)
              },
            },
          },
        },
      },
    })

    const canvas = wrapper.findComponent({ name: 'DrawingCanvas' })
    await wrapper.find('.emit-drawing').trigger('click')

    expect(canvas.emitted('executed')).toEqual([[drawing]])
  })
})
```

- [x] **Step 2: Run App test to verify failure**

Run from `frontend/`:

```bash
npm run test -- src/App.test.js
```

Expected: FAIL because `App.vue` does not hold a canvas ref or handle `drawing` events.

- [x] **Step 3: Implement App coordination**

Update `frontend/src/App.vue`:

```vue
<script setup lang="ts">
import { ref } from 'vue'
import VoiceControl from './components/VoiceControl.vue'
import DrawingCanvas from './components/DrawingCanvas.vue'

const drawingCanvas = ref<InstanceType<typeof DrawingCanvas> | null>(null)

function handleDrawing(drawing: unknown) {
  const result = drawingCanvas.value?.executeDrawing(drawing)
  if (result?.message) {
    console.info(result.message)
  }
}
</script>

<template>
  <main class="min-h-screen px-4 py-8">
    <VoiceControl @drawing="handleDrawing" />
    <DrawingCanvas ref="drawingCanvas" />
  </main>
</template>
```

- [x] **Step 4: Run App test to verify pass**

Run from `frontend/`:

```bash
npm run test -- src/App.test.js
```

Expected: PASS.

- [x] **Step 5: Commit App coordination**

```bash
git add frontend/src/App.vue frontend/src/App.test.js
git commit -m "feat(frontend): wire voice drawing results to canvas"
```

- [ ] **Step 6: Mark OpenSpec wiring task complete**

Change this checkbox in `openspec/changes/execute-drawing-instructions/tasks.md`:

```markdown
- [ ] Wire voice results to drawing execution and display backend messages for non-draw/error envelopes without changing the canvas.
```

to:

```markdown
- [x] Wire voice results to drawing execution and display backend messages for non-draw/error envelopes without changing the canvas.
```

Commit:

```bash
git add openspec/changes/execute-drawing-instructions/tasks.md
git commit -m "chore(openspec): mark voice to canvas wiring complete"
```

## Task 6: Focused Test Coverage Completion

**Files:**
- Modify: `openspec/changes/execute-drawing-instructions/tasks.md:1-8`

- [ ] **Step 1: Run all focused backend and frontend tests**

Run from `backend/`:

```bash
.venv/Scripts/python -m pytest tests/test_interpret_drawing_endpoint.py tests/test_drawing_interpreter.py -v
```

Expected: PASS.

Run from `frontend/`:

```bash
npm run test -- src/api/__tests__/drawingInterpreter.test.js src/components/__tests__/DrawingCanvas.test.ts src/components/__tests__/VoiceControl.test.js src/App.test.js
```

Expected: PASS.

- [ ] **Step 2: Mark focused coverage task complete**

Change this checkbox in `openspec/changes/execute-drawing-instructions/tasks.md`:

```markdown
- [ ] Add focused tests or verification coverage for successful basic creation, non-draw message handling, and unsupported actions not crashing the UI.
```

to:

```markdown
- [x] Add focused tests or verification coverage for successful basic creation, non-draw message handling, and unsupported actions not crashing the UI.
```

- [ ] **Step 3: Commit focused coverage status**

```bash
git add openspec/changes/execute-drawing-instructions/tasks.md
git commit -m "chore(openspec): mark focused drawing coverage complete"
```

## Task 7: Build and Manual Verification

**Files:**
- Modify: `openspec/changes/execute-drawing-instructions/tasks.md:1-8`

- [ ] **Step 1: Run backend validation**

Run from `backend/`:

```bash
.venv/Scripts/python -m pytest tests/ -v
```

Expected: PASS.

- [ ] **Step 2: Run frontend validation**

Run from `frontend/`:

```bash
npm run test
npm run build
```

Expected: both commands PASS.

- [ ] **Step 3: Manually verify UI golden path**

Start backend from `backend/`:

```bash
.venv/Scripts/python -m uvicorn main:app --reload
```

Start frontend from `frontend/`:

```bash
npm run dev
```

In the browser:

1. Open the Vite dev URL.
2. Start listening.
3. Speak or otherwise produce a transcript equivalent to `画一个蓝色圆形在画布中央`.
4. Confirm the recognition history still shows the transcript.
5. Confirm the Network panel shows a POST to `/api/interpret-drawing` with `{ "text": "..." }`.
6. Confirm the canvas adds a visible circle.
7. Produce unsupported/no-op input such as `把圆形旋转45度` or non-drawing text.
8. Confirm a message appears and the canvas object count does not change.

- [ ] **Step 4: Mark final verification task complete**

Change this checkbox in `openspec/changes/execute-drawing-instructions/tasks.md`:

```markdown
- [ ] Run the relevant frontend/backend validation commands and manually verify the golden path in the browser if UI execution is implemented.
```

to:

```markdown
- [x] Run the relevant frontend/backend validation commands and manually verify the golden path in the browser if UI execution is implemented.
```

- [ ] **Step 5: Commit verification status**

```bash
git add openspec/changes/execute-drawing-instructions/tasks.md
git commit -m "chore(openspec): mark drawing execution verification complete"
```

## Final Build Gate

- [ ] **Step 1: Confirm all OpenSpec tasks are checked**

Run:

```bash
grep -n '\- \[ \]' openspec/changes/execute-drawing-instructions/tasks.md
```

Expected: no output.

- [ ] **Step 2: Request code review if using executing-plans**

If `build_mode` is `executing-plans`, load `requesting-code-review` before running the build guard. Fix CRITICAL findings before continuing. If the skill is unavailable, append this exact marker to `openspec/changes/execute-drawing-instructions/tasks.md` and commit it:

```markdown
<!-- review skipped: skill unavailable -->
```

- [ ] **Step 3: Run build guard**

Run:

```bash
COMET_ENV="${COMET_ENV:-$(find . "$HOME"/.*/skills "$HOME/.config" "$HOME/.gemini" -path '*/comet/scripts/comet-env.sh' -type f -print -quit 2>/dev/null)}" && . "$COMET_ENV" && "$COMET_BASH" "$COMET_GUARD" execute-drawing-instructions build --apply
```

Expected: ALL CHECKS PASSED and `.comet.yaml` advances to `phase: verify`.

## Self-Review

- Spec coverage: Task 1 covers backend standalone endpoint contract; Task 2 covers transcript submission to `/api/interpret-drawing`; Task 3 covers controlled canvas execution for rectangle/circle/text/line and unsupported action safety; Tasks 4-5 cover voice-to-canvas wiring and non-draw message behavior; Tasks 6-7 cover focused and full validation.
- Placeholder scan: no `TBD`, open-ended “add tests”, or undefined helper names remain; each code-changing step includes concrete code.
- Type consistency: `interpretDrawingText`, `executeDrawing`, drawing envelope fields, and emitted `drawing` event names are consistent across tasks.
