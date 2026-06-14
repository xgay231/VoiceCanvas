import { ref } from "vue";
import { MicVAD } from "@ricky0123/vad-web";
import ortWasmModuleUrl from "onnxruntime-web/ort-wasm-simd-threaded.mjs?url";
import ortWasmBinaryUrl from "onnxruntime-web/ort-wasm-simd-threaded.wasm?url";
import { encodeWav } from "../utils/wav-encoder.js";

/**
 * Voice capture composable.
 *
 * Manages MicVAD lifecycle (audio capture + Silero VAD), encodes speech
 * segments to WAV, and sends them to the backend /api/asr endpoint.
 *
 * @returns {{ status: Ref, results: Ref, error: Ref, start: () => Promise<void>, stop: () => void }}
 */
export function useVoiceCapture() {
  /** @type {import('vue').Ref<'idle' | 'listening' | 'speaking' | 'processing' | 'error'>} */
  const status = ref("idle");

  /** @type {import('vue').Ref<Array<{ text: string, timestamp: number }>>} */
  const results = ref([]);

  /** @type {import('vue').Ref<string | null>} */
  const error = ref(null);

  /** @type {MicVAD | null} */
  let vad = null;

  /** @type {MediaStream | null} */
  let stream = null;

  /** Maximum number of retry attempts for ASR requests */
  const MAX_RETRIES = 3;

  /** Retry delays in milliseconds (exponential backoff: 1s, 2s, 4s) */
  const RETRY_DELAYS = [1000, 2000, 4000];

  /**
   * Send audio to backend ASR endpoint with automatic retry.
   * @param {Blob} audioBlob - WAV audio blob
   * @param {number} attempt - Current attempt number (0-based)
   */
  async function sendToAsr(audioBlob, attempt = 0) {
    const formData = new FormData();
    formData.append("audio", audioBlob, "speech.wav");

    try {
      const response = await fetch("/api/asr", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (data.success && data.text) {
        results.value = [
          ...results.value,
          { text: data.text, timestamp: Date.now() },
        ];
        status.value = "listening";
      } else if (attempt < MAX_RETRIES) {
        await delay(RETRY_DELAYS[attempt]);
        return sendToAsr(audioBlob, attempt + 1);
      } else {
        error.value = data.error || "ASR recognition failed";
        status.value = "error";
      }
    } catch (err) {
      if (attempt < MAX_RETRIES) {
        await delay(RETRY_DELAYS[attempt]);
        return sendToAsr(audioBlob, attempt + 1);
      }
      error.value = err.message || "Network error";
      status.value = "error";
    }
  }

  /**
   * Process a speech segment: encode to WAV and send to ASR.
   * @param {Float32Array} audio - Raw PCM samples from MicVAD (16kHz, mono)
   */
  async function processAudio(audio) {
    status.value = "processing";
    const wavBlob = encodeWav(audio, 16000);
    await sendToAsr(wavBlob);
  }

  /**
   * Start voice capture.
   * Requests microphone permission, creates MicVAD, and begins listening.
   */
  async function start() {
    try {
      error.value = null;
      status.value = "idle";

      vad = await MicVAD.new({
        baseAssetPath: "/",
        onnxWASMBasePath: {
          mjs: ortWasmModuleUrl,
          wasm: ortWasmBinaryUrl,
        },
        startOnLoad: false,
        redemptionMs: 3000,
        getStream: async () => {
          stream = await navigator.mediaDevices.getUserMedia({
            audio: {
              channelCount: 1,
              echoCancellation: true,
              autoGainControl: true,
              noiseSuppression: true,
            },
          });
          return stream;
        },
        pauseStream: async (mediaStream) => {
          mediaStream.getTracks().forEach((track) => track.stop());
        },
        resumeStream: async () => {
          stream = await navigator.mediaDevices.getUserMedia({
            audio: {
              channelCount: 1,
              echoCancellation: true,
              autoGainControl: true,
              noiseSuppression: true,
            },
          });
          return stream;
        },
        onSpeechStart: () => {
          status.value = "speaking";
        },
        onSpeechEnd: (audio) => {
          status.value = "processing";
          processAudio(audio);
        },
        onVADMisfire: () => {
          // Brief noise detected but not actual speech — ignore
        },
      });

      await vad.start();
      status.value = "listening";
    } catch (err) {
      if (err.name === "NotAllowedError") {
        error.value =
          "Microphone permission denied. Please allow microphone access and try again.";
      } else {
        error.value = err.message || "Failed to start voice capture";
      }
      status.value = "error";
    }
  }

  /**
   * Stop voice capture and release resources.
   */
  function stop() {
    if (vad) {
      vad.destroy().catch(() => {});
      vad = null;
    }
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    status.value = "idle";
  }

  return { status, results, error, start, stop };
}

/**
 * Utility: returns a promise that resolves after `ms` milliseconds.
 */
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
