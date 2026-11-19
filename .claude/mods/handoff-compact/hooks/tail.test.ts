import type { SessionMessage } from 'claude-code'
import { expect, test } from 'claude-code/testing'
import { keepTail, MIN_KEPT, sizeOf, slim, WHOLE_WEIGHT } from './tail.ts'

const prompt = (text: string): SessionMessage => ({ role: 'user', text, toolUses: [] })
const reply = (text: string): SessionMessage => ({ role: 'assistant', text, toolUses: [] })
const result: SessionMessage = {
  role: 'user',
  text: '',
  toolUses: [],
  toolResults: [{ tool_use_id: 't1', text: 'ok', isError: false }] as SessionMessage['toolResults'],
}

const talk = [prompt('one'), reply('a'), prompt('two'), reply('b'), result, reply('c'), prompt('three'), reply('d')]
const size = (list: SessionMessage[]) => list.reduce((n, m) => n + sizeOf(m), 0)
// Where the cut lands, with every message at its plain size.
const cut = (list: SessionMessage[], budget: number) => keepTail(list, budget, 0, 1)

test('counts a tool output once: the result the model read, not its stored record', () => {
  const call: SessionMessage = {
    role: 'assistant',
    text: 'ab',
    toolUses: [{ tool_use_id: 't1', tool: 'Read', input: { file_path: '/x' }, text: 'z'.repeat(500), result: { content: 'z'.repeat(500) } }],
  } as SessionMessage
  const answer: SessionMessage = {
    role: 'user',
    text: '',
    toolUses: [],
    toolResults: [{ tool_use_id: 't1', text: 'z'.repeat(500), isError: false, result: { content: 'z'.repeat(500) } }],
  } as SessionMessage
  expect(sizeOf(call)).toBe(2 + JSON.stringify({ file_path: '/x' }).length)
  expect(sizeOf(answer)).toBe(500)
})

test('keeps everything that fits', () => {
  expect(cut(talk, 100_000)).toEqual(talk)
})

test('never opens on a tool result: the cut moves back to the prompt', () => {
  const tail = cut(talk, size(talk.slice(2)))
  expect(tail?.map(m => m.text)).toEqual(['two', 'b', '', 'c', 'three', 'd'])
})

test('stops at the budget, keeping the oldest safe start that fits', () => {
  expect(cut(talk, size(talk.slice(-2)))?.map(m => m.text)).toEqual(['three', 'd'])
})

test('opens on an assistant message when the cut would land on a tool result', () => {
  expect(cut(talk, size(talk.slice(4)))?.map(m => m.text)).toEqual(['c', 'three', 'd'])
})

test('an autonomous run with no recent prompt still keeps its newest tool calls', () => {
  const run = [prompt('go'), ...Array.from({ length: 50 }, (_, i) => [reply(`call ${i}`), result]).flat()]
  const tail = cut(run, size(run.slice(-4)))
  expect(tail?.[0]?.role).toBe('assistant')
  expect(tail?.map(m => m.text)).toEqual(['call 48', '', 'call 49', ''])
})

test('slim drops the handle of all but the newest messages, keeping their text and tool blocks', () => {
  const stamped = talk.map((m, i) => ({ ...m, handle: `h${i}` }))
  const out = slim(stamped, 2)
  expect(out.map(m => m.handle)).toEqual([undefined, undefined, undefined, undefined, undefined, undefined, 'h6', 'h7'])
  expect(out.map(m => m.text)).toEqual(talk.map(m => m.text))
  expect(out[4]?.toolResults).toEqual(result.toolResults)
  expect('handle' in (out[0] ?? {})).toBe(false)
})

test('slim keeps the whole current turn: from the last prompt on, however long', () => {
  const run = [prompt('one'), reply('a'), prompt('go'), ...Array.from({ length: 6 }, () => [reply('call'), result]).flat()]
  const out = slim(run.map((m, i) => ({ ...m, handle: `h${i}` })), 2)
  expect(out.map(m => m.handle !== undefined)).toEqual([false, false, ...Array(13).fill(true)])
})

test('slim keeps a tail with no prompt whole: it is all the current turn', () => {
  const run = [reply('call'), result, reply('call'), result, reply('done')].map((m, i) => ({ ...m, handle: `h${i}` }))
  expect(slim(run, 2)).toEqual(run)
})

test('slim keeps everything whole when the tail is not longer than the whole count', () => {
  const stamped = talk.slice(-2).map((m, i) => ({ ...m, handle: `h${i}` }))
  expect(slim(stamped, 4)).toEqual(stamped)
})

test('messages kept whole weigh WHOLE_WEIGHT: an autonomous run keeps fewer of them', () => {
  const run = [prompt('go'), ...Array.from({ length: 50 }, (_, i) => [reply(`call ${i}`), result]).flat()]
  const budget = size(run.slice(-40))
  expect(keepTail(run, budget, 0)?.length).toBeLessThan(40)
  expect(keepTail(run, budget * WHOLE_WEIGHT, 0)).toHaveLength(40)
  expect(keepTail(run, budget * WHOLE_WEIGHT - 1, 0)?.length).toBeLessThan(40)
})

test('turns before the last prompt weigh their text alone: they are rebuilt without thinking', () => {
  const old = Array.from({ length: 10 }, (_, i) => [prompt(`p${i}`), reply(`r${i}`)]).flat()
  const talk2 = [...old, prompt('now'), reply('doing')]
  const budget = size(old) + size(talk2.slice(-2)) * WHOLE_WEIGHT
  expect(keepTail(talk2, budget, 0)).toEqual(talk2)
  expect(keepTail(talk2, budget - 1, 0)).not.toEqual(talk2)
})

test('the newest `whole` messages weigh WHOLE_WEIGHT even after the prompt', () => {
  const tail2 = [...Array.from({ length: 10 }, (_, i) => [prompt(`p${i}`), reply(`r${i}`)]).flat(), prompt('c'), reply('d')]
  const budget = size(tail2.slice(0, -3)) + size(tail2.slice(-3)) * WHOLE_WEIGHT
  expect(keepTail(tail2, budget, 3)).toEqual(tail2)
  expect(keepTail(tail2, budget - 1, 3)).not.toEqual(tail2)
})

test('a parallel tool batch too big weighted is kept at its plain size instead of falling back', () => {
  const batch: SessionMessage = { ...reply('reads'), toolUses: [] }
  const results: SessionMessage = {
    ...result,
    toolResults: Array.from({ length: 14 }, (_, i) => ({ tool_use_id: `t${i}`, text: 'x'.repeat(3_000), isError: false })),
  } as SessionMessage
  const run = [prompt('go'), reply('a'), batch, results]
  const budget = size([batch, results])
  expect(keepTail(run, budget, 4)?.map(m => m.text)).toEqual(['reads', ''])
  expect(keepTail(run, budget - 1, 4)).toBeNull()
})

test('a weighted cut that keeps fewer than MIN_KEPT messages falls back to the plain size', () => {
  const run = [prompt('go'), ...Array.from({ length: 20 }, (_, i) => [reply(`call ${i}`), result]).flat()]
  const budget = size(run.slice(-MIN_KEPT))
  expect(keepTail(run, budget, 0)).toHaveLength(MIN_KEPT)
})

test('null when nothing safe fits', () => {
  expect(cut(talk, 0)).toBeNull()
  expect(cut([result], 100_000)).toBeNull()
})
