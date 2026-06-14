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
