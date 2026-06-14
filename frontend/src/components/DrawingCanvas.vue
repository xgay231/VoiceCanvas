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
