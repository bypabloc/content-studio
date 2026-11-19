import { expect, test } from 'claude-code/testing'
import { bandText, headline, keepsMessage, spinnerWord } from './status.ts'

test('the band appends the context fill, and draws the fill alone without bound work', () => {
  expect(bandText({ work: 'w', status: 'in-progress', eta: '~2 h' }, 42)).toBe('in-progress · ETA ~2 h · ctx 42%')
  expect(bandText(null, 7)).toBe('ctx 7%')
  expect(bandText({ work: 'w', status: 'done' }, null)).toBe('done')
  expect(bandText(null, null)).toBeNull()
})

const full = {
  work: '157-clinic-roles',
  status: 'in-progress',
  phase: 'verification',
  done: 'F1 to F3',
  current: 'commit 5',
  remaining: 'PR and merge',
  eta: '~2 h',
  next_step: 'run the battery',
}

test('headline is the status alone: status, phase and ETA, without the work name or the reason', () => {
  // La 157 escribía párrafos en Status: la banda ocupaba media pantalla con el motivo y Done/Current/Remaining.
  expect(headline({ ...full, reason: 'commit ca7d100 en feat/157-7…' })).toBe('in-progress · verification · ETA ~2 h')
})

test('a blocked headline keeps its reason: it is what the person has to act on', () => {
  expect(headline({ work: 'w', status: 'blocked', reason: 'credentials: the signing .p12', eta: '~1 h' })).toBe(
    'blocked · credentials: the signing .p12 · ETA ~1 h',
  )
  expect(headline({ work: 'w', status: 'blocked' })).toBe('blocked')
})

test('spinner word prefers Current, falls back to the next step, null when empty', () => {
  expect(spinnerWord(full)).toBe('verification · commit 5 · ETA ~2 h')
  expect(spinnerWord({ work: 'w', next_step: 'push' })).toBe('push')
  expect(spinnerWord({ work: 'w' })).toBeNull()
})

test('a hook progress message is stale and yields to the work word; other engine messages stay', () => {
  expect(keepsMessage('Running SessionStart hooks…')).toBe(false)
  expect(keepsMessage('Running PostToolUse hooks...')).toBe(false)
  expect(keepsMessage('Compacting conversation')).toBe(true)
  expect(keepsMessage(undefined)).toBe(false)
})
