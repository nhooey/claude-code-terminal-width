import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

// The width the model was last told; null until it has been.
const told = atom({ plugin: 'terminal-width', key: 'told' } as const, null)

export const register: Register = on => {
  // The width the terminal last drew the prompt band at. A plain variable,
  // since a render hook may not write state; after a reload it is unknown
  // until the band's next draw, which comes with the next screen update.
  let columns: number | null = null

  // Measure only: the band above the prompt is drawn on every screen and
  // again after each resize, and this hook adds nothing to it.
  on('ui.render', { component: 'AbovePrompt' }, ($, e, next) => {
    const width = e.viewport?.columns
    if (width !== undefined && width > 0) {
      columns = width
    }
    return next(e)
  })

  // Tell the model in a row of the conversation, not the system prompt: a
  // thread's system prompt is fixed once sent, so a changed width there
  // would never reach it. A row only goes in when the width has changed.
  on('prompt.submit', async ($, e, next) => {
    const width = columns
    if (width !== null && width !== (await read($, told))) {
      const note = {
        type: 'text',
        text: `The terminal is ${width} columns wide. Fit tables and other laid-out text to that width.`,
      } as const
      const appended = await $.session.append({ message: { type: 'user', content: [note] } })
      if (!('deny' in appended)) {
        await update($, told, () => width)
      }
    }
    return next(e)
  }).catch(($, e, next) => next(e)) // a failure here must never hold up the prompt
}
