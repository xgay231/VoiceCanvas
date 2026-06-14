// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import App from './App.vue'

describe('App drawing coordination', () => {
  const drawing = {
    version: '1.0',
    type: 'draw',
    actions: [{ action: 'create', shape: 'circle', params: {} }],
    requires_clarification: false,
    message: null,
  }

  function mountAppWithCanvasResult(result) {
    return mount(App, {
      global: {
        stubs: {
          VoiceControl: {
            name: 'VoiceControl',
            emits: ['drawing'],
            template: '<button class="emit-drawing" @click="$emit(\'drawing\', drawing)">emit</button>',
            data: () => ({ drawing }),
          },
          DrawingCanvas: {
            name: 'DrawingCanvas',
            template: '<div class="drawing-canvas"></div>',
            methods: {
              executeDrawing(drawingEnvelope) {
                this.$emit('executed', drawingEnvelope)
                return result
              },
            },
          },
        },
      },
    })
  }

  it('passes draw envelopes from VoiceControl to DrawingCanvas', async () => {
    const wrapper = mountAppWithCanvasResult({ executed: 1, skipped: 0, message: null })

    const canvas = wrapper.findComponent({ name: 'DrawingCanvas' })
    await wrapper.find('.emit-drawing').trigger('click')

    expect(canvas.emitted('executed')).toEqual([[drawing]])
  })

  it('shows canvas execution messages to the user', async () => {
    const wrapper = mountAppWithCanvasResult({ executed: 0, skipped: 1, message: '部分绘图指令暂不支持，已跳过。' })

    await wrapper.find('.emit-drawing').trigger('click')

    expect(wrapper.text()).toContain('部分绘图指令暂不支持，已跳过。')
  })
})
