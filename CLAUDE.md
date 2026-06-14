# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VoiceCanvas is a voice-powered text recognition app: Vue 3 frontend captures speech via browser VAD, sends WAV audio to a FastAPI backend, which transcribes it using Xiaomi's MIMO ASR model (OpenAI-compatible API).

## Commands

**Frontend** (run from `frontend/`):

```bash
npm run dev        # Vite dev server on port 5173 (proxies /api → localhost:8000)
npm run build      # Production build
npm run test       # Vitest (single run)
npx vitest         # Vitest (watch mode)
```

**Backend** (run from `backend/`, use `.venv/Scripts/python` on Windows):

```bash
pip install -r requirements.txt                # Install deps (first time)
uvicorn main:app --reload                      # Dev server on port 8000
pytest tests/ -v                               # Run all tests
pytest tests/test_asr.py::test_function_name   # Run single test
```

Requires `backend/.env` with `MIMO_API_KEY` and `MIMO_BASE_URL` (see `.env.example`).

## Architecture

```
frontend/ (Vue 3 + Vite)          backend/ (FastAPI)
  VoiceControl.vue                   main.py
       │                                │
  useVoiceCapture.js               POST /api/asr
  (MicVAD + ONNX in browser)           │
       │                           MIMO ASR API
  wav-encoder.js                   (OpenAI-compatible)
```

**Voice capture flow**: MicVAD (Silero VAD model via ONNX Runtime WASM in browser) detects speech segments → encodes to 16kHz mono 16-bit WAV → POSTs to `/api/asr` with retry (3 attempts, exponential backoff 1s/2s/4s).

**Backend flow**: Receives WAV upload → base64 encodes → sends to MIMO ASR via OpenAI chat completions format → returns `{text, success}`.

## Key Details

- **Audio format contract**: 16kHz, mono, 16-bit PCM WAV. The `wav-encoder.js` utility handles conversion; any changes must preserve these parameters.
- **ONNX/VAD assets** in `frontend/public/` are large binaries (`.onnx`, `.wasm`). Do not modify; they are loaded at runtime by `@ricky0123/vad-web`.
- **CORS** is configured in `backend/main.py` for `localhost:5173` and `localhost:3000` (both `http://` and `http://127.0.0.1`).
- **No linter or formatter** is configured. Code style is inferred from existing patterns.

## CodeGraph

A `.codegraph/` index exists. Use `codegraph_explore` MCP tool (or `codegraph explore "<query>"` in shell) before reading files — it returns verbatim source with call paths in one call.
