/** Status lines of the bound work's PROGRESS.md, as `session_handoff.py --status` prints them. */
export type WorkStatus = {
  work: string
  status?: string
  reason?: string
  phase?: string
  done?: string
  current?: string
  remaining?: string
  eta?: string
  next_step?: string
}

declare module 'claude-code' {
  interface PluginState {
    'handoff-compact': { status: WorkStatus | null; isHidden: boolean; contextPercent: number | null }
  }
}
