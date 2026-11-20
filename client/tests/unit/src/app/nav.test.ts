import { describe, expect, it } from 'vitest'

import { navItems } from '@/app/nav'
import { t } from '@/shared/i18n/t'

describe('navItems (spec 009, AC-3)', () => {
  it('WHEN the sections are listed THEN each one has its icon name from the map of UIIcon', () => {
    expect(navItems().map((item) => [item.id, item.icon])).toEqual([
      ['narration', 'narration'],
      ['voices', 'voices'],
      ['settings', 'settings'],
    ])
  })

  it('spec 010 (D-6): Mis voces va en el grupo Voces', () => {
    expect(navItems().find((item) => item.id === 'voices')).toMatchObject({
      group: t('nav.group.voices'),
      label: t('nav.voices'),
    })
  })
})
