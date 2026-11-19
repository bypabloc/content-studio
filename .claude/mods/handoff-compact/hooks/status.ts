import type { WorkStatus } from '../types'

/** Theme color of each work status; anything else draws as plain text. */
export const STATUS_COLOR: Record<string, 'success' | 'warning' | 'suggestion'> = {
  'in-progress': 'suggestion',
  blocked: 'warning',
  done: 'success',
}

/** Joins the present parts with a middle dot, skipping the missing ones. */
const joined = (parts: Array<string | undefined>): string => parts.filter(Boolean).join(' · ')

/**
 * The band's only row: status, phase and ETA. The reason shows only while blocked, the one time the person has to
 * act on it; the work name and Done/Current/Remaining are left out (the spinner already says what runs now).
 */
export function headline(status: WorkStatus): string {
  const reason = status.status === 'blocked' ? status.reason : undefined
  return joined([status.status, reason, status.phase, status.eta && `ETA ${status.eta}`])
}

/**
 * The band's text: the work's headline, then the context window's fill (`ctx 42%`). Null when neither is known,
 * so no band draws: no bound work and no response yet in a fresh or just compacted window.
 */
export function bandText(status: WorkStatus | null, percent: number | null): string | null {
  const text = joined([status ? headline(status) : undefined, percent === null ? undefined : `ctx ${percent}%`])
  return text === '' ? null : text
}

/**
 * The spinner's word while a turn runs: the phase and what is being done now, so
 * the line reads `verification · commit 5 · ETA ~2 h… (1m 25s · ↓ 6.4k tokens)`.
 * Null when PROGRESS.md has neither, so the engine keeps its own word.
 */
export function spinnerWord(status: WorkStatus): string | null {
  const word = joined([status.phase, status.current ?? status.next_step, status.eta && `ETA ${status.eta}`])
  return word === '' ? null : word.slice(0, 90)
}

/**
 * Whether the spinner keeps the engine's own message instead of the work word.
 * «Running <Event> hooks…» stays on the spinner after the hooks finish, so it
 * reads as if they were still running; it yields. Any other message is kept.
 */
export function keepsMessage(message: string | null | undefined): boolean {
  return Boolean(message) && !/^Running \w+ hooks/.test(message ?? '')
}
