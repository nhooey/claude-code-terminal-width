import { expect, mock, test } from 'claude-code/testing'

const BAND = {
  plugin: 'terminal-width',
  surface: 'terminal',
  component: 'AbovePrompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 10,
    bodyColumns: 115,
    scroll: { offset: 0, bodyRows: 10 },
    view: {},
  },
} as const

// A prompt as the engine raises one typed at the terminal.
const prompt = (text: string) => ({ text, wait: false, origin: { kind: 'composer' } }) as const

const notes = (rows: ReturnType<ReturnType<typeof mock.session>['appended']>) =>
  rows.map(row => JSON.stringify(row.message)).filter(text => text.includes('columns wide'))

test('the model is told the width once, and again after a resize', async ($, on) => {
  const session = mock.session(on)
  on('prompt.submit', (_, e) => ({ text: e.text }))
  // Stands for the engine's own drawing of the band.
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })

  // Nothing measured yet: nothing to tell.
  await $.prompt.submit(prompt('first'))
  expect(notes(session.appended())).toHaveLength(0)

  const band = await $.ui.mount({ ...BAND, viewport: { columns: 120, rows: 40 } })
  await band.unmount()
  await $.prompt.submit(prompt('second'))
  await $.prompt.submit(prompt('third'))
  expect(notes(session.appended())).toHaveLength(1)
  expect(notes(session.appended())[0]).toContain('The terminal is 120 columns wide')

  const resized = await $.ui.mount({ ...BAND, viewport: { columns: 90, rows: 40 } })
  await resized.unmount()
  await $.prompt.submit(prompt('fourth'))
  expect(notes(session.appended())).toHaveLength(2)
  expect(notes(session.appended())[1]).toContain('The terminal is 90 columns wide')
})
