<script setup lang="ts">
import { ref } from 'vue'
import VoiceControl from './components/VoiceControl.vue'
import DrawingCanvas from './components/DrawingCanvas.vue'

const drawingCanvas = ref<InstanceType<typeof DrawingCanvas> | null>(null)
const executionMessage = ref(null)

function handleDrawing(drawing: unknown) {
  executionMessage.value = null
  const result = drawingCanvas.value?.executeDrawing(drawing)
  if (result?.message) {
    executionMessage.value = result.message
  }
}
</script>

<template>
  <main class="min-h-screen px-4 py-8">
    <VoiceControl @drawing="handleDrawing" />
    <p v-if="executionMessage" class="mx-auto mb-4 max-w-[880px] text-center text-sm text-blue-700">
      {{ executionMessage }}
    </p>
    <DrawingCanvas ref="drawingCanvas" />
  </main>
</template>
