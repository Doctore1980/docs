import { expect, test } from 'claude-code/testing'

const USO = { input_tokens: 1, output_tokens: 1, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 }

const BAND = {
  plugin: 'mejorar-prompt',
  component: 'AbovePrompt',
  props: { hasSurvey: false, view: {} },
} as const

test('los botones reescriben el borrador según el modo y permiten deshacer', async ($, on) => {
  let sistema = ''
  let rellenado = ''
  on('prompt.read', () => ({ value: { text: 'resume evidencia linfadenectomía', cursor: 0 } }))
  on('model.complete', (_, e) => {
    sistema = String(e.system ?? '')
    return { value: { isAnswered: true, text: '```\nPROMPT MEJORADO\n```', usage: USO } }
  })
  on('prompt.fill', (_, e) => {
    rellenado = e.text
    return { isFilled: true }
  })

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface } as never)
    await ui.press({ key: 'cientifico' })
    expect(sistema).toContain('CIENTÍFICO')
    expect(rellenado).toBe('PROMPT MEJORADO')

    await ui.press({ key: 'deshacer' })
    expect(rellenado).toBe('resume evidencia linfadenectomía')

    await ui.press({ key: 'creativo' })
    expect(sistema).toContain('CREATIVO')
    await ui.unmount()
  }
})

test('el comando /mejorar usa el modo indicado y sin texto muestra la ayuda', async ($, on) => {
  let sistema = ''
  let rellenado = ''
  on('command.register', () => ({ value: { command: 'mejorar' } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('model.complete', (_, e) => {
    sistema = String(e.system ?? '')
    return { value: { isAnswered: true, text: 'Versión creativa', usage: USO } }
  })
  on('prompt.fill', (_, e) => {
    rellenado = e.text
    return { isFilled: true }
  })

  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  const ayuda = await $.command.run({ command: 'mejorar', args: '' })
  expect(ayuda.text ?? '').toContain('Uso: /mejorar')

  const r = await $.command.run({ command: 'mejorar', args: 'creativo título para una charla de robótica' })
  expect(sistema).toContain('CREATIVO')
  expect(rellenado).toBe('Versión creativa')
  expect(r.text ?? '').toContain('Creativo')
})
