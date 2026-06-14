// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'

const {
  mockAdd,
  mockSetActiveObject,
  mockRenderAll,
  mockDispose,
  MockRect,
  MockCircle,
  MockText,
  MockLine,
} = vi.hoisted(() => {
  class MockRect {
    constructor(public opts: unknown) {}
  }

  class MockCircle {
    constructor(public opts: unknown) {}
  }

  class MockText {
    constructor(public text: string, public opts: unknown) {}
  }

  class MockLine {
    constructor(public points: number[], public opts: unknown) {}
  }

  return {
    mockAdd: vi.fn(),
    mockSetActiveObject: vi.fn(),
    mockRenderAll: vi.fn(),
    mockDispose: vi.fn(),
    MockRect,
    MockCircle,
    MockText,
    MockLine,
  }
})

vi.mock('fabric', () => {
  const mockWrapper = document.createElement('div')
  return {
    fabric: {
      Canvas: class MockCanvas {
        add = mockAdd
        setActiveObject = mockSetActiveObject
        renderAll = mockRenderAll
        dispose = mockDispose
        wrapperEl = mockWrapper
      },
      Rect: MockRect,
      Circle: MockCircle,
      Text: MockText,
      Line: MockLine,
    },
  }
})

import DrawingCanvas from '../DrawingCanvas.vue'

describe('DrawingCanvas', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders a canvas element', () => {
    const wrapper = mount(DrawingCanvas)
    const canvasEl = wrapper.find('canvas')
    expect(canvasEl.exists()).toBe(true)
  })

  it('initializes Fabric Canvas on mount', () => {
    const wrapper = mount(DrawingCanvas)
    expect(wrapper.vm.canvas).toBeDefined()
    expect(wrapper.vm.canvas).not.toBeNull()
  })

  it('adds a default shape after initialization', () => {
    mount(DrawingCanvas)
    expect(mockAdd).toHaveBeenCalled()
    expect(mockSetActiveObject).toHaveBeenCalled()
  })

  it('exposes canvas instance via defineExpose', () => {
    const wrapper = mount(DrawingCanvas)
    const canvasInstance = wrapper.vm.canvas
    expect(canvasInstance).toBeDefined()
    expect(canvasInstance).toHaveProperty('add')
    expect(canvasInstance).toHaveProperty('dispose')
    expect(canvasInstance).toHaveProperty('renderAll')
  })

  it('executes supported create actions and renders the canvas', () => {
    const wrapper = mount(DrawingCanvas)
    vi.clearAllMocks()

    const result = wrapper.vm.executeDrawing({
      version: '1.0',
      type: 'draw',
      actions: [
        { action: 'create', shape: 'rectangle', params: { x: 100, y: 120, width: 80, height: 40, fill: '#2563eb' } },
        { action: 'create', shape: 'circle', params: { x: 200, y: 220, radius: 30, fill: 'blue' } },
        { action: 'create', shape: 'text', params: { x: 300, y: 320, text: '你好', fontSize: 24 } },
        { action: 'create', shape: 'line', params: { x1: 10, y1: 20, x2: 110, y2: 120, stroke: '#111827' } },
      ],
    })

    expect(result).toEqual({ executed: 4, skipped: 0, message: null })
    expect(mockAdd).toHaveBeenCalledTimes(4)
    expect(mockSetActiveObject).toHaveBeenCalledTimes(4)
    expect(mockRenderAll).toHaveBeenCalledTimes(1)
  })

  it('skips unsupported actions without throwing', () => {
    const wrapper = mount(DrawingCanvas)
    vi.clearAllMocks()

    const result = wrapper.vm.executeDrawing({
      version: '1.0',
      type: 'draw',
      actions: [
        { action: 'update', shape: 'rectangle', params: {} },
        { action: 'create', shape: 'triangle', params: {} },
      ],
    })

    expect(result).toEqual({ executed: 0, skipped: 2, message: '部分绘图指令暂不支持，已跳过。' })
    expect(mockAdd).not.toHaveBeenCalled()
    expect(mockRenderAll).not.toHaveBeenCalled()
  })

  it('does not execute non-draw envelopes', () => {
    const wrapper = mount(DrawingCanvas)
    vi.clearAllMocks()

    const result = wrapper.vm.executeDrawing({
      version: '1.0',
      type: 'no_op',
      actions: [{ action: 'create', shape: 'circle', params: {} }],
      message: '不是绘图指令',
    })

    expect(result).toEqual({ executed: 0, skipped: 1, message: '不是绘图指令' })
    expect(mockAdd).not.toHaveBeenCalled()
  })

  it('disposes canvas on unmount', () => {
    const wrapper = mount(DrawingCanvas)
    wrapper.unmount()
    expect(mockDispose).toHaveBeenCalled()
  })

  it('renders a download button', () => {
    const wrapper = mount(DrawingCanvas)
    const button = wrapper.find('button')
    expect(button.exists()).toBe(true)
    expect(button.text()).toContain('下载')
  })
})
