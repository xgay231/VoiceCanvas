/**
 * Encode Float32Array PCM samples into a WAV Blob.
 *
 * @param {Float32Array} samples - PCM samples in range [-1.0, 1.0]
 * @param {number} sampleRate - Sample rate in Hz (e.g. 16000)
 * @returns {Blob} WAV file as a Blob with type "audio/wav"
 */
export function encodeWav(samples, sampleRate) {
  const numChannels = 1
  const bitsPerSample = 16
  const bytesPerSample = bitsPerSample / 8
  const dataLength = samples.length * bytesPerSample
  const headerLength = 44
  const buffer = new ArrayBuffer(headerLength + dataLength)
  const view = new DataView(buffer)

  // RIFF chunk descriptor
  writeString(view, 0, 'RIFF')
  view.setUint32(4, buffer.byteLength - 8, true) // chunk size
  writeString(view, 8, 'WAVE')

  // fmt sub-chunk
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true) // sub-chunk 1 size (PCM = 16)
  view.setUint16(20, 1, true) // audio format: 1 = PCM
  view.setUint16(22, numChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * numChannels * bytesPerSample, true) // byte rate
  view.setUint16(32, numChannels * bytesPerSample, true) // block align
  view.setUint16(34, bitsPerSample, true)

  // data sub-chunk
  writeString(view, 36, 'data')
  view.setUint32(40, dataLength, true)

  // Write PCM samples (float32 -> int16)
  let offset = 44
  for (let i = 0; i < samples.length; i++) {
    // Clamp to [-1, 1] then scale to int16 range
    const s = Math.max(-1, Math.min(1, samples[i]))
    const val = s < 0 ? s * 0x7fff : s * 0x7fff
    view.setInt16(offset, val, true)
    offset += 2
  }

  return new Blob([buffer], { type: 'audio/wav' })
}

/**
 * Write an ASCII string into a DataView at the given offset.
 */
function writeString(view, offset, str) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i))
  }
}
