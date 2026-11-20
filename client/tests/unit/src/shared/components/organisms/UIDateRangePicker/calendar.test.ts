/** Tests for the pure calendar helpers of the date range picker (spec 126, AC-35).
 *
 * @author Pablo Contreras
 * @since 2026/10/31
 */

import { describe, expect, it } from 'vitest'

import { clamp, fromIso, monthMatrix, pickDay, presetRange, previewRange, referenceDay, shiftDay, toIso, weekEdge } from '@/shared/components/organisms/UIDateRangePicker'

describe('calendar [AC-35]', () => {
  it('WHEN monthMatrix THEN 6 weeks starting on Monday [AC-35]', () => {
    const weeks = monthMatrix(2026, 9)
    expect(weeks).toHaveLength(6)
    expect(weeks.every((week) => week.length === 7)).toBe(true)
    expect(weeks[0]?.[0]).toBe('2026-09-28')
    expect(weeks[5]?.[6]).toBe('2026-11-08')
  })

  it('WHEN presetRange(lastMonth) on 2026-10-31 THEN 2026-09-01..2026-09-30 [AC-35]', () => {
    expect(presetRange('lastMonth', new Date(Date.UTC(2026, 9, 31, 12)))).toEqual({ from: '2026-09-01', to: '2026-09-30' })
  })

  it('WHEN a preset passes max THEN it is clamped [AC-35]', () => {
    const range = presetRange('last7', new Date(Date.UTC(2026, 9, 2, 12)))
    expect(clamp(range, undefined, '2026-10-01')).toEqual({ from: '2026-09-26', to: '2026-10-01' })
  })

  it('WHEN clamp has a min THEN the start is raised to it [AC-35]', () => {
    expect(clamp({ from: '2026-09-01', to: '2026-09-30' }, '2026-09-10', undefined)).toEqual({ from: '2026-09-10', to: '2026-09-30' })
  })

  it('WHEN the second day is before the first THEN the pick swaps them [AC-35]', () => {
    expect(pickDay({ from: '2026-10-09', to: null }, '2026-10-03')).toEqual({ from: '2026-10-03', to: '2026-10-09' })
  })

  it('WHEN a complete range is picked from THEN the next day starts a new range [AC-35]', () => {
    expect(pickDay({ from: '2026-10-03', to: '2026-10-09' }, '2026-10-20')).toEqual({ from: '2026-10-20', to: null })
  })

  it('WHEN only the start is set THEN the preview spans it to the hovered day [AC-35]', () => {
    expect(previewRange({ from: '2026-10-09', to: null }, '2026-10-03')).toEqual({ from: '2026-10-03', to: '2026-10-09' })
    expect(previewRange({ from: '2026-10-09', to: null }, null)).toBeNull()
    expect(previewRange({ from: '2026-10-03', to: '2026-10-09' }, '2026-10-20')).toBeNull()
  })

  it('WHEN a day is shifted or moved to a week edge THEN the date follows the calendar [AC-35]', () => {
    expect(shiftDay('2026-10-31', 1)).toBe('2026-11-01')
    expect(weekEdge('2026-10-31', 'start')).toBe('2026-10-26')
    expect(weekEdge('2026-10-31', 'end')).toBe('2026-11-01')
  })

  it('WHEN toIso and fromIso round trip THEN the same UTC day comes back [AC-35]', () => {
    expect(toIso(fromIso('2026-02-28'))).toBe('2026-02-28')
  })

  it('WHEN no reference day is injected THEN the current day is used [AC-35]', () => {
    expect(toIso(referenceDay())).toBe(toIso(new Date()))
    expect(referenceDay(new Date(Date.UTC(2026, 9, 31, 12)))).toEqual(new Date(Date.UTC(2026, 9, 31, 12)))
  })

  it('WHEN the instant is already the next UTC day THEN today and this month follow the UTC calendar [AC-35]', () => {
    const nextUtcDay = new Date('2026-11-01T02:00:00Z')
    expect(toIso(nextUtcDay)).toBe('2026-11-01')
    expect(presetRange('today', nextUtcDay)).toEqual({ from: '2026-11-01', to: '2026-11-01' })
    expect(presetRange('thisMonth', nextUtcDay)).toEqual({ from: '2026-11-01', to: '2026-11-01' })
  })

  it('WHEN a day is read from ISO THEN its UTC getters return the same day [AC-35]', () => {
    const day = fromIso('2026-10-01')
    expect([day.getUTCFullYear(), day.getUTCMonth(), day.getUTCDate()]).toEqual([2026, 9, 1])
  })
})
