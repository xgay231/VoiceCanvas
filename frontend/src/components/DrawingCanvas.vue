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

  // Fabric.js replaces the original <canvas> with its own wrapper div.
  // Apply border/background styles to the Fabric wrapper so they're visible.
  const wrapper = fabricCanvas.wrapperEl
  wrapper.classList.add('block', 'border', 'border-slate-400', 'bg-slate-50', 'shadow-md')
})

onUnmounted(() => {
  if (!canvas.value) {
    return
  }

  canvas.value.dispose()
  canvas.value = null
})

defineExpose({ canvas, executeDrawing })
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
        :width="CANVAS_WIDTH"
        :height="CANVAS_HEIGHT"
      />
    </div>
  </section>
</template>
