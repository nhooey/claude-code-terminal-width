import { expect, mock, test } from 'claude-code/testing'
import type { Engine, TestBody } from 'claude-code/testing'

type On = Parameters<TestBody>[1]

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

// The text of each width note among the appended rows.
const notes = (rows: readonly { message: { content: readonly unknown[] } }[]) =>
  rows.map(row => JSON.stringify(row.message.content)).filter(text => text.includes('columns wide'))

// Stands for the engine beneath the mod: draws the band and takes each
// prompt, recording the text that reached it.
const engine = (on: On) => {
  const submitted: string[] = []
  on('prompt.submit', (_, e) => {
    submitted.push(e.text)
    return { text: e.text }
  })
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
  return submitted
}

// Draws the band once at the given viewport, as the terminal does on a
// screen update or a resize.
const draw = async ($: Engine, viewport: { columns: number; rows: number } | undefined) => {
  const band = await $.ui.mount({ ...BAND, viewport } as Parameters<typeof $.ui.mount>[0])
  await band.unmount()
}

test('nothing is told before the band has been measured', async ($, on) => {
  const session = mock.session(on)
  engine(on)

  await $.prompt.submit(prompt('first'))

  expect(notes(session.appended())).toEqual([])
})

test('the measured width is told before the next prompt', async ($, on) => {
  const session = mock.session(on)
  engine(on)

  await draw($, { columns: 120, rows: 40 })
  await $.prompt.submit(prompt('first'))

  const told = notes(session.appended())
  expect(told).toHaveLength(1)
  expect(told[0]).toContain('The terminal is 120 columns wide. Fit tables and other laid-out text to that width.')
})

test('an unchanged width is not told again', async ($, on) => {
  const session = mock.session(on)
  engine(on)

  await draw($, { columns: 120, rows: 40 })
  await $.prompt.submit(prompt('first'))
  await draw($, { columns: 120, rows: 40 })
  await $.prompt.submit(prompt('second'))

  expect(notes(session.appended())).toHaveLength(1)
})

test('a new width after a resize is told', async ($, on) => {
  const session = mock.session(on)
  engine(on)

  await draw($, { columns: 120, rows: 40 })
  await $.prompt.submit(prompt('first'))
  await draw($, { columns: 90, rows: 40 })
  await $.prompt.submit(prompt('second'))

  const told = notes(session.appended())
  expect(told).toHaveLength(2)
  expect(told[1]).toContain('The terminal is 90 columns wide')
})

test('a draw with no usable viewport keeps the last width', async ($, on) => {
  const session = mock.session(on)
  engine(on)

  await draw($, { columns: 120, rows: 40 })
  await draw($, undefined)
  await draw($, { columns: 0, rows: 0 })
  await $.prompt.submit(prompt('first'))

  const told = notes(session.appended())
  expect(told).toHaveLength(1)
  expect(told[0]).toContain('The terminal is 120 columns wide')
})

test('a draw with no usable viewport alone tells nothing', async ($, on) => {
  const session = mock.session(on)
  engine(on)

  await draw($, undefined)
  await draw($, { columns: 0, rows: 0 })
  await $.prompt.submit(prompt('first'))

  expect(notes(session.appended())).toEqual([])
})

test('the prompt text reaches the engine unchanged', async ($, on) => {
  mock.session(on)
  const submitted = engine(on)

  await $.prompt.submit(prompt('before'))
  await draw($, { columns: 120, rows: 40 })
  await $.prompt.submit(prompt('after'))

  expect(submitted).toEqual(['before', 'after'])
})

test('a refused note is told again on the next prompt', async ($, on) => {
  const stored: { message: { content: readonly unknown[] } }[] = []
  let refuse = true
  on('session.append', { door: 'note' }, async ($, e, next) => {
    if (refuse) {
      return { deny: 'refused by the test' }
    }
    const row = await next(e)
    stored.push(e)
    return row
  })
  engine(on)

  await draw($, { columns: 120, rows: 40 })
  await $.prompt.submit(prompt('first'))
  expect(notes(stored)).toEqual([])

  refuse = false
  await $.prompt.submit(prompt('second'))
  const told = notes(stored)
  expect(told).toHaveLength(1)
  expect(told[0]).toContain('The terminal is 120 columns wide')
})

// Refusing the write of the told width makes the mod's hook throw after it
// appended the note. (A throwing session.append hook of the test's won't do:
// the kit drops it and stores the row anyway.)
test('a failure while telling never holds up the prompt', async ($, on) => {
  on('state.set', () => ({ deny: 'refused by the test' }) as never)
  const submitted = engine(on)

  await draw($, { columns: 120, rows: 40 })
  await $.prompt.submit(prompt('first'))

  expect(submitted).toEqual(['first'])
})
