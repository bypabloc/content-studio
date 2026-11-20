import { describe, expect, it } from 'vitest'

import { formatClock, parseClock } from '@/features/music/parseClock'

describe('parseClock (spec 011, D-4, AC-6)', () => {
  it('WHEN a clock is typed THEN it reads mm:ss, m:ss, ss and one decimal as seconds', () => {
    expect(parseClock('00:49.3')).toBe(49.3)
    expect(parseClock('1:30')).toBe(90)
    expect(parseClock('45')).toBe(45)
    expect(parseClock('2:05.5')).toBe(125.5)
  })

  it('WHEN the text is not a clock THEN it returns null', () => {
    expect(parseClock('')).toBeNull()
    expect(parseClock('abc')).toBeNull()
    expect(parseClock('1:75')).toBeNull()
    expect(parseClock('1:30.25')).toBeNull()
  })

  it('WHEN seconds are formatted THEN they show mm:ss.d rounded to tenths', () => {
    expect(formatClock(49.3)).toBe('00:49.3')
    expect(formatClock(49.300000000000004)).toBe('00:49.3')
    expect(formatClock(90)).toBe('01:30.0')
    expect(formatClock(59.96)).toBe('01:00.0')
  })

  it('WHEN a formatted clock is read back THEN it gives the same seconds', () => {
    expect(parseClock(formatClock(302))).toBe(302)
  })
})
