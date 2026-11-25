import { describe, expect, it } from 'vitest'

import { navItems } from '@/app/nav'
import { t } from '@/shared/i18n/t'

describe('navItems (spec 009, AC-3)', () => {
  it('WHEN the sections are listed THEN each one has its icon name from the map of UIIcon', () => {
    expect(navItems().map((item) => [item.id, item.icon])).toEqual([
      ['narration', 'narration'],
      ['music', 'music'],
      ['transcription', 'transcription'],
      ['cleaner', 'scissors'],
      ['subtitles', 'subtitles'],
      ['convert', 'download'],
      ['normalize', 'volume'],
      ['mix', 'mix'],
      ['editor', 'editor'],
      ['library', 'library'],
      ['voices', 'voices'],
      ['catalog', 'layers'],
      ['engines', 'server'],
      ['settings', 'settings'],
    ])
  })

  it('spec 010 (D-6): Mis voces y Catálogo van en el grupo Voces', () => {
    expect(navItems().find((item) => item.id === 'voices')).toMatchObject({
      group: t('nav.group.voices'),
      label: t('nav.voices'),
    })
    expect(navItems().find((item) => item.id === 'catalog')).toMatchObject({
      group: t('nav.group.voices'),
      label: t('nav.catalog'),
    })
  })

  it('spec 016 (D-4): Mezcla va en el grupo Editar', () => {
    expect(navItems().find((item) => item.id === 'mix')).toMatchObject({
      group: t('nav.group.edit'),
      label: t('nav.mix'),
    })
  })

  it('spec 017: Editor va en el grupo Editar', () => {
    expect(navItems().find((item) => item.id === 'editor')).toMatchObject({
      group: t('nav.group.edit'),
      label: t('nav.editor'),
    })
  })

  it('Motores queda en el grupo Ajustes', () => {
    expect(navItems().find((item) => item.id === 'engines')).toMatchObject({
      group: t('nav.group.settings'),
      label: t('nav.engines'),
    })
  })
})

describe('navItems (spec 036, D-1)', () => {
  it('WHEN the sections are listed THEN Transcripción is in Editar, before Limpiador', () => {
    expect(navItems().find((item) => item.id === 'transcription')).toMatchObject({
      group: t('nav.group.edit'),
      label: t('nav.transcription'),
    })
    const ids = navItems().map((item) => item.id)
    expect(ids.indexOf('transcription')).toBe(ids.indexOf('cleaner') - 1)
  })
})
