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

<template>
  <div class="voice-control">
    <h1>VoiceCanvas</h1>
    <p class="subtitle">Voice-powered text recognition</p>

    <!-- Status indicator -->
    <div class="status" :class="status">
      <span class="status-icon">
        <template v-if="status === 'idle'">&#127908;</template>
        <template v-else-if="status === 'listening'">&#127908;</template>
        <template v-else-if="status === 'speaking'">&#128308;</template>
        <template v-else-if="status === 'processing'">&#9203;</template>
        <template v-else-if="status === 'error'">&#9888;&#65039;</template>
      </span>
      <span class="status-text">
        <template v-if="status === 'idle'">Not started</template>
        <template v-else-if="status === 'listening'">Listening...</template>
        <template v-else-if="status === 'speaking'">Speaking</template>
        <template v-else-if="status === 'processing'">Recognizing...</template>
        <template v-else-if="status === 'error'">Error</template>
      </span>
    </div>

    <!-- Error message -->
    <p v-if="error" class="error-msg">{{ error }}</p>
    <p v-if="drawingMessage" class="drawing-msg">{{ drawingMessage }}</p>

    <!-- Toggle button -->
    <button class="toggle-btn" :class="{ active: status !== 'idle' && status !== 'error' }" @click="toggle">
      {{ status === 'idle' || status === 'error' ? 'Start Listening' : 'Stop' }}
    </button>

    <!-- Results list -->
    <div v-if="results.length > 0" ref="resultsContainer" class="results">
      <div v-for="(item, index) in results" :key="index" class="result-item">
        <span class="result-time">{{ new Date(item.timestamp).toLocaleTimeString() }}</span>
        <span class="result-text">{{ item.text }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.voice-control {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

h1 {
  margin: 0 0 0.25rem;
  font-size: 2rem;
}

.subtitle {
  margin: 0 0 2rem;
  color: #666;
}

.status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.status.listening .status-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.error-msg {
  color: #d32f2f;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.drawing-msg {
  color: #1d4ed8;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.toggle-btn {
  padding: 0.75rem 2rem;
  font-size: 1rem;
  border: 2px solid #1a73e8;
  border-radius: 2rem;
  background: #fff;
  color: #1a73e8;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 2rem;
}

.toggle-btn:hover {
  background: #e8f0fe;
}

.toggle-btn.active {
  background: #d32f2f;
  border-color: #d32f2f;
  color: #fff;
}

.toggle-btn.active:hover {
  background: #b71c1c;
}

.results {
  text-align: left;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
}

.result-item {
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  gap: 0.75rem;
  align-items: baseline;
}

.result-item:last-child {
  border-bottom: none;
}

.result-time {
  color: #999;
  font-size: 0.8rem;
  white-space: nowrap;
}

.result-text {
  color: #333;
  font-size: 1rem;
}
</style>
