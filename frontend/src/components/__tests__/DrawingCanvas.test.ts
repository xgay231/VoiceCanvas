// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'

const mockAdd = vi.fn()
const mockSetActiveObject = vi.fn()
const mockRenderAll = vi.fn()
const mockDispose = vi.fn()

const mockCanvas = {
  add: mockAdd,
  setActiveObject: mockSetActiveObject,
  renderAll: mockRenderAll,
  dispose: mockDispose,
}

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
      Rect: class MockRect {
        constructor(public opts: unknown) {}
      },
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
    // After mount, canvas ref should be set to a Fabric Canvas instance
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
