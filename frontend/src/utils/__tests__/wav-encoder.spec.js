import { describe, it, expect } from 'vitest'
import { encodeWav } from '../wav-encoder.js'

describe('encodeWav', () => {
  it('returns a Blob with WAV content', () => {
    const samples = new Float32Array([0, 0.5, -0.5, 1.0, -1.0])
    const blob = encodeWav(samples, 16000)
    expect(blob).toBeInstanceOf(Blob)
    expect(blob.type).toBe('audio/wav')
  })

  it('produces a valid RIFF/WAVE header', async () => {
    const samples = new Float32Array(160) // 10ms at 16kHz
    const blob = encodeWav(samples, 16000)
    const buffer = await blob.arrayBuffer()
    const view = new DataView(buffer)

    // "RIFF" magic
    const riff = String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3))
    expect(riff).toBe('RIFF')

    // "WAVE" format
    const wave = String.fromCharCode(view.getUint8(8), view.getUint8(9), view.getUint8(10), view.getUint8(11))
    expect(wave).toBe('WAVE')

    // "fmt " subchunk
    const fmt = String.fromCharCode(view.getUint8(12), view.getUint8(13), view.getUint8(14), view.getUint8(15))
    expect(fmt).toBe('fmt ')

    // Audio format = 1 (PCM)
    expect(view.getUint16(20, true)).toBe(1)
    // Num channels = 1 (mono)
    expect(view.getUint16(22, true)).toBe(1)
    // Sample rate = 16000
    expect(view.getUint32(24, true)).toBe(16000)
    // Bits per sample = 16
    expect(view.getUint16(34, true)).toBe(16)
  })

  it('calculates correct file size', async () => {
    const samples = new Float32Array(100)
    const blob = encodeWav(samples, 16000)
    const buffer = await blob.arrayBuffer()
    const view = new DataView(buffer)

    // File size = 44 header + 100 samples * 2 bytes = 244
    // RIFF chunk size = file size - 8 = 236
    expect(view.getUint32(4, true)).toBe(236)
    // Data chunk size = 100 * 2 = 200
    expect(view.getUint32(40, true)).toBe(200)
    expect(buffer.byteLength).toBe(244)
  })

  it('converts float samples to 16-bit PCM correctly', async () => {
    const samples = new Float32Array([1.0, -1.0, 0.0])
    const blob = encodeWav(samples, 16000)
    const buffer = await blob.arrayBuffer()
    const view = new DataView(buffer)

    // PCM data starts at byte 44
    // 1.0 -> 32767
    expect(view.getInt16(44, true)).toBe(32767)
    // -1.0 -> -32767
    expect(view.getInt16(46, true)).toBe(-32767)
    // 0.0 -> 0
    expect(view.getInt16(48, true)).toBe(0)
  })

  it('clamps out-of-range samples', async () => {
    const samples = new Float32Array([2.0, -2.0])
    const blob = encodeWav(samples, 16000)
    const buffer = await blob.arrayBuffer()
    const view = new DataView(buffer)

    // Clamped to 1.0 -> 32767
    expect(view.getInt16(44, true)).toBe(32767)
    // Clamped to -1.0 -> -32767
    expect(view.getInt16(46, true)).toBe(-32767)
  })
})
