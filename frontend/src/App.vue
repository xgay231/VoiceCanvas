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
