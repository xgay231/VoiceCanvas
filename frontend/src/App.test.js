// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import App from './App.vue'

describe('App drawing coordination', () => {
  it('passes draw envelopes from VoiceControl to DrawingCanvas', async () => {
    const drawing = {
      version: '1.0',
      type: 'draw',
      actions: [{ action: 'create', shape: 'circle', params: {} }],
      requires_clarification: false,
      message: null,
    }

    const wrapper = mount(App, {
      global: {
        stubs: {
          VoiceControl: {
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
              },
            },
          },
        },
      },
    })

    const canvas = wrapper.findComponent({ name: 'DrawingCanvas' })
    await wrapper.find('.emit-drawing').trigger('click')

    expect(canvas.emitted('executed')).toEqual([[drawing]])
  })
})
