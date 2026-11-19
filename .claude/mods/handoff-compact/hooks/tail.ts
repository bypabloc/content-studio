import type { SessionMessage } from 'claude-code'

/**
 * Rough size of a message in characters, counting each piece the model reads once: its text, the
 * arguments of its tool calls and the text of its tool results. A call's stored `result` and `text`
 * repeat the answer that the next message's `toolResults` already carries, so they are left out.
 * Thinking blocks and attachments (nested rules) are not in a SessionMessage: the real tail is bigger.
 */
export const sizeOf = (message: SessionMessage): number =>
  message.text.length +
  message.toolUses.reduce((n, use) => n + JSON.stringify(use.input).length, 0) +
  (message.toolResults ?? []).reduce((n, result) => n + result.text.length, 0)

/**
 * Hands back all but the `whole` newest messages without their engine handle, so the engine rebuilds
 * them from role, text and tool blocks: their thinking blocks and the attachments riding on them (nested
 * rules, ~90 % of a real tail) are dropped. The current turn stays whole, from the last prompt on
 * (all of a tail with no prompt): the API needs every thinking block of a tool loop unmodified.
 */
export function slim(tail: readonly SessionMessage[], whole: number): SessionMessage[] {
  const turn = tail.findLastIndex(m => m.role === 'user' && opensTurn(m))
  const from = Math.max(0, Math.min(turn, tail.length - whole))
  return tail.map((message, i) => {
    if (i >= from) return message
    const { handle: _handle, ...rebuilt } = message
    return rebuilt
  })
}

/**
 * A safe place to open the tail: any assistant message (its tool results come
 * after it) or a user message with text and no tool result. Only a user message
 * carrying tool results is unsafe, because its calls would be cut off.
 */
const opensTurn = (message: SessionMessage): boolean =>
  message.role === 'assistant' ||
  (message.text.trim() !== '' && (message.toolResults?.length ?? 0) === 0)

/**
 * Weight in the budget of a message that `slim` hands back whole: its thinking blocks and attachments ride
 * along unseen by `sizeOf`. With 1, an autonomous run (all one turn) kept 188 whole messages and the first
 * call after the cut read 151k tokens; the 0.2.0 estimator, which counted each tool output ~3 times, read ~95k.
 */
export const WHOLE_WEIGHT = 3

/**
 * Fewest messages a weighted cut may keep before the plain size is tried: at 157.3 → 157.4 the weight left 6
 * of 1006 and the next calls reread the plan and three services.
 */
export const MIN_KEPT = 12

/**
 * The newest stretch of the conversation that fits in `budget` characters, each message kept whole weighing
 * WHOLE_WEIGHT (the current turn from the last prompt on, and the `whole` newest), and that
 * opens on a safe message (`opensTurn`), so no tool result loses its call. In an
 * autonomous run, with no prompt for hours, the tail opens on an assistant turn.
 * Null when not even the newest such stretch fits: the caller then falls back to
 * the summarizer.
 */
export function keepTail(
  messages: readonly SessionMessage[],
  budget: number,
  whole: number,
  weight = WHOLE_WEIGHT,
): SessionMessage[] | null {
  let size = 0
  let start = -1
  let pastPrompt = false
  messages.findLast((message, i) => {
    const isWhole = !pastPrompt || i >= messages.length - whole
    size += sizeOf(message) * (isWhole ? weight : 1)
    if (message.role === 'user' && opensTurn(message)) pastPrompt = true
    if (size > budget) return true
    if (opensTurn(message)) start = i
    return false
  })
  // A big parallel tool batch can outweigh the budget on its own: keep it at its plain size rather than pay
  // for a model summary (a 14-file batch fell back and the first call after it read 163k instead of ~92k).
  const kept = start < 0 ? null : messages.slice(start)
  if (weight > 1 && (kept?.length ?? 0) < MIN_KEPT) {
    const plain = keepTail(messages, budget, whole, 1)
    if ((plain?.length ?? 0) > (kept?.length ?? 0)) return plain
  }
  return kept
}
