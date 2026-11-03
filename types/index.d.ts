/** A width in terminal columns, or null before one is known. */
export type Columns = number | null

declare module 'claude-code' {
  interface PluginState {
    'terminal-width': { told: Columns }
  }
}
