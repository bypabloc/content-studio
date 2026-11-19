import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, SessionMessage } from 'claude-code'

import type { WorkStatus } from '../types'
import { bandText, keepsMessage, spinnerWord, STATUS_COLOR } from './status.ts'
import { keepTail, slim } from './tail.ts'

// ponytail: chars/4 ≈ tokens; ~20k tokens kept verbatim (OpenCode keeps 15k). The real tail is bigger:
// thinking and nested rules ride along unseen. Measure with `compact-stats --since` before raising it.
const TAIL_BUDGET = 80_000
// Newest messages handed back whole, with their thinking; the older ones are rebuilt without it.
const WHOLE = 4
// Must match HEADER in .agents/hooks/handoff_text.py.
const BOUND = '[session-handoff] Trabajo '
const MARKER =
  '[handoff-compact] Conversation compacted without a summary. The session handoff comes separately ' +
  '(SessionStart compact) and wins over what follows; check it against git status and git log. ' +
  'What follows are the newest messages, unsummarized. If the work is not finished, continue now ' +
  'with the next step: budget or token warnings are not a limit.'
const ACK = 'Understood.'

const status = atom({ plugin: 'handoff-compact', key: 'status' } as const, null)
const isHidden = atom({ plugin: 'handoff-compact', key: 'isHidden' } as const, false)
const contextPercent = atom({ plugin: 'handoff-compact', key: 'contextPercent' } as const, null)

/** The repo's handoff script, or null outside git. */
async function scriptOf($: EngineInterface): Promise<{ cwd: string; script: string } | null> {
  const cwd = await $.session.cwd()
  const top = await $.process.run(['git', 'rev-parse', '--show-toplevel'], { cwd })
  if (top.exitCode !== 0) return null
  return { cwd, script: `${top.stdout.trim()}/.agents/hooks/session_handoff.py` }
}

/** Runs the handoff script with `args` and the session's id and cwd on stdin; null on failure. */
async function runScript($: EngineInterface, args: string[], extra: Record<string, unknown>): Promise<string | null> {
  const found = await scriptOf($)
  if (!found) return null
  const payload = { session_id: await $.session.id(), cwd: found.cwd, ...extra }
  // uv finds a Python on Windows and WSL alike (`python3` is a Store stub on Windows).
  const run = await $.process.run(['uv', 'run', '--no-project', 'python', found.script, ...args], {
    cwd: found.cwd,
    stdin: JSON.stringify(payload),
    timeoutMs: 10_000,
  })
  return run.exitCode === 0 ? run.stdout : null
}

/**
 * Whether the repo's handoff hook has bound work for this session: the same
 * text SessionStart:compact injects right after the compaction. `probe` keeps
 * this check out of the handoff log.
 */
async function hasHandoff($: EngineInterface): Promise<boolean> {
  const out = await runScript($, [], { hook_event_name: 'SessionStart', source: 'compact', probe: true })
  if (!out?.trim()) return false
  const text: unknown = JSON.parse(out)?.hookSpecificOutput?.additionalContext
  return typeof text === 'string' && text.startsWith(BOUND)
}

/** Appends the mod's decision to tmp/handoff/.log/events.jsonl; never throws. */
async function logDecision($: EngineInterface, event: Record<string, unknown>): Promise<void> {
  try {
    await runScript($, ['--log'], { ...event, agent: 'claude', mod: $.plugin.name })
  } catch {
    // The log is evidence, not a gate: a failure here must not block the compaction.
  }
}

/** Rereads the bound work's status lines into the state the band and spinner draw. */
async function refresh($: EngineInterface): Promise<void> {
  try {
    const parsed: unknown = JSON.parse((await runScript($, ['--status'], {})) ?? '{}')
    const next = parsed && typeof parsed === 'object' && 'work' in parsed ? (parsed as WorkStatus) : null
    await update($, status, () => next)
  } catch {
    // A broken status line must not break the session: the band just stays as it was.
  }
}

const built = (role: SessionMessage['role'], text: string): SessionMessage => ({ role, text, toolUses: [] })

/**
 * Compacts from the handoff without the summarizer, and keeps the bound work's
 * status in view: the spinner's word while a turn runs, and a band above the
 * prompt with status, phase and ETA from PROGRESS.md and the context window's fill.
 */
export const register: Register = on => {
  on('session.compact', async ($, e, next) => {
    if (e.trigger === 'precompute') return { skip: `${$.plugin.name}: compacts on demand from the handoff` }
    const total = e.messages.length
    if (e.agentId !== undefined) {
      await logDecision($, { event: 'compact.fallback', reason: 'subagent', trigger: e.trigger, total })
      return next(e)
    }
    if (!(await hasHandoff($))) {
      await logDecision($, { event: 'compact.fallback', reason: 'no-handoff', trigger: e.trigger, total })
      return next(e)
    }
    const tail = keepTail(e.messages, TAIL_BUDGET, WHOLE)
    if (!tail) {
      await logDecision($, { event: 'compact.fallback', reason: 'tail-too-big', trigger: e.trigger, total })
      return next(e)
    }
    const kept = slim(tail, WHOLE)
    const whole = kept.filter(m => m.handle !== undefined).length
    await logDecision($, { event: 'compact.kept', trigger: e.trigger, kept: kept.length, whole, total })
    $.ui.toast(`${$.plugin.name}: ${kept.length} of ${total} messages kept (${whole} whole), no summary`)
    // Roles must alternate: an assistant-led tail follows the marker directly.
    const ack = kept[0]?.role === 'assistant' ? [] : [built('assistant', ACK)]
    return { messages: [built('user', MARKER), ...ack, ...kept] }
  })

  on('session.start', async ($, e, next) => {
    await refresh($)
    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    await refresh($)
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    await refresh($)
    return next(e)
  })

  // ponytail: rereads after every Write or Edit, not only PROGRESS.md; a path filter if it ever shows up as slow.
  on('tool.call', async ($, e, next) => {
    const result = await next(e)
    if (e.tool === 'Write' || e.tool === 'Edit') await refresh($)
    return result
  })

  // The engine measures after each response; the band redraws only when the whole percent moves.
  on('session.measure', async ($, e, next) => {
    const percent = e.context.percent ?? null
    if ((await read($, contextPercent)) !== percent) await update($, contextPercent, () => percent)
    return next(e)
  })

  on('ui.render', { component: 'Spinner' }, async ($, e, next) => {
    const current = await read($, status)
    const word = current && !keepsMessage(e.props.message) ? spinnerWord(current) : null
    return next(word ? ({ ...e, props: { ...e.props, word, message: null } } as typeof e) : e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const current = await read($, status)
    const text = bandText(current, await read($, contextPercent))
    if (e.props.hasSurvey || text === null || (await read($, isHidden))) return next(e)
    const { Box, Button, Text } = $.ui.resolve(e)
    return (
      <Box>
        <Text bold wrap="truncate-end" color={STATUS_COLOR[current?.status ?? ''] ?? 'text'}>
          ● {text}{' '}
        </Text>
        <Button key="hide" label="Hide" onPress={() => update($, isHidden, () => true)} />
      </Box>
    )
  })
}
