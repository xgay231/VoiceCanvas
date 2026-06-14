// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'

const mockResults = ref([])
const mockStatus = ref('idle')
const mockError = ref(null)
const mockStart = vi.fn()
const mockStop = vi.fn()
const mockInterpretDrawingText = vi.fn()

vi.mock('../../composables/useVoiceCapture.js', () => ({
  useVoiceCapture: () => ({
    status: mockStatus,
    results: mockResults,
    error: mockError,
    start: mockStart,
    stop: mockStop,
  }),
}))

vi.mock('../../api/drawingInterpreter.js', () => ({
  interpretDrawingText: (...args) => mockInterpretDrawingText(...args),
}))

import VoiceControl from '../VoiceControl.vue'

enableAutoUnmount(afterEach)

describe('VoiceControl drawing interpretation', () => {
  beforeEach(() => {
    mockResults.value = []
    mockStatus.value = 'idle'
    mockError.value = null
    mockStart.mockReset()
    mockStop.mockReset()
    mockInterpretDrawingText.mockReset()
  })

  it('submits new transcript text to the drawing interpretation endpoint', async () => {
    mockInterpretDrawingText.mockResolvedValue({
      version: '1.0',
      type: 'draw',
      actions: [],
      requires_clarification: false,
      message: null,
    })
    mount(VoiceControl)

    mockResults.value = [{ text: '画一个圆', timestamp: 1 }]
    await flushPromises()

    expect(mockInterpretDrawingText).toHaveBeenCalledWith('画一个圆')
  })

  it('emits draw envelopes for App coordination', async () => {
    const drawing = {
      version: '1.0',
      type: 'draw',
      actions: [{ action: 'create', shape: 'circle', params: {} }],
      requires_clarification: false,
      message: null,
    }
    mockInterpretDrawingText.mockResolvedValue(drawing)
    const wrapper = mount(VoiceControl)

    mockResults.value = [{ text: '画一个圆', timestamp: 1 }]
    await flushPromises()

    expect(wrapper.emitted('drawing')).toEqual([[drawing]])
  })

  it('shows non-draw drawing messages without emitting draw envelopes', async () => {
    mockInterpretDrawingText.mockResolvedValue({
      version: '1.0',
      type: 'unsupported',
      actions: [],
      requires_clarification: false,
      message: '暂不支持旋转操作',
    })
    const wrapper = mount(VoiceControl)

    mockResults.value = [{ text: '旋转图形', timestamp: 1 }]
    await flushPromises()

    expect(wrapper.text()).toContain('暂不支持旋转操作')
    expect(wrapper.emitted('drawing')).toBeUndefined()
  })

  it('ignores stale interpretation responses for older transcripts', async () => {
    let resolveFirst
    let resolveSecond
    mockInterpretDrawingText
      .mockReturnValueOnce(new Promise((resolve) => { resolveFirst = resolve }))
      .mockReturnValueOnce(new Promise((resolve) => { resolveSecond = resolve }))
    const wrapper = mount(VoiceControl)

    mockResults.value = [{ text: '画一个圆', timestamp: 1 }]
    await nextTick()
    await nextTick()
    expect(mockInterpretDrawingText).toHaveBeenCalledTimes(1)
    mockResults.value = [
      { text: '画一个圆', timestamp: 1 },
      { text: '画一个矩形', timestamp: 2 },
    ]
    await nextTick()
    await nextTick()
    expect(mockInterpretDrawingText).toHaveBeenCalledTimes(2)

    resolveSecond({
      version: '1.0',
      type: 'draw',
      actions: [{ action: 'create', shape: 'rectangle', params: {} }],
      requires_clarification: false,
      message: null,
    })
    await flushPromises()
    resolveFirst({
      version: '1.0',
      type: 'draw',
      actions: [{ action: 'create', shape: 'circle', params: {} }],
      requires_clarification: false,
      message: null,
    })
    await flushPromises()

    expect(wrapper.emitted('drawing')).toEqual([[
      {
        version: '1.0',
        type: 'draw',
        actions: [{ action: 'create', shape: 'rectangle', params: {} }],
        requires_clarification: false,
        message: null,
      },
    ]])
  })
})
