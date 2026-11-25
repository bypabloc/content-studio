import { describe, expect, it } from 'vitest'

import { OPEN_SECTIONS, parseExternal } from '@/app/external/parseExternal'
import { navItems } from '@/app/nav'

const EXE = 'content-studio.exe'

describe('parseExternal (spec 031, F1 C1)', () => {
  it('WHEN no hay ningún enlace en argv THEN no hay petición', () => {
    expect(parseExternal([EXE])).toBeNull()
  })

  it('AC-1: WHEN se abre content-studio://open/music THEN pide abrir Música', () => {
    expect(parseExternal([EXE, 'content-studio://open/music'])).toEqual({ kind: 'open', section: 'music' })
  })

  it('AC-4: WHEN la sección no existe THEN es un error', () => {
    expect(parseExternal([EXE, 'content-studio://open/nope'])).toMatchObject({ kind: 'error' })
  })

  it('AC-4: WHEN la acción no existe THEN es un error', () => {
    expect(parseExternal([EXE, 'content-studio://engine/install'])).toMatchObject({ kind: 'error' })
  })

  it('AC-4: WHEN new trae un tipo fuera de la lista THEN es un error', () => {
    expect(parseExternal([EXE, 'content-studio://new/engine.install?name=x'])).toMatchObject({ kind: 'error' })
  })

  it('AC-4: WHEN new trae un parámetro fuera de la lista THEN es un error', () => {
    expect(parseExternal([EXE, 'content-studio://new/narration?text=hola&shell=calc'])).toMatchObject({ kind: 'error' })
  })

  it('AC-4: WHEN la URL pasa de 4096 caracteres THEN es un error', () => {
    const long = `content-studio://new/narration?text=${'a'.repeat(4096)}`
    expect(parseExternal([EXE, long])).toMatchObject({ kind: 'error' })
  })

  it('AC-4: WHEN la URL tiene segmentos de más THEN es un error', () => {
    expect(parseExternal([EXE, 'content-studio://open/music/extra'])).toMatchObject({ kind: 'error' })
  })

  it('AC-2: WHEN se abre job/<id> o library/<id> THEN pide ese id', () => {
    expect(parseExternal([EXE, 'content-studio://job/42'])).toEqual({ kind: 'job', id: 42 })
    expect(parseExternal([EXE, 'content-studio://library/7'])).toEqual({ kind: 'library', id: 7 })
  })

  it('AC-2: WHEN el id no es un entero positivo THEN es un error', () => {
    expect(parseExternal([EXE, 'content-studio://job/abc'])).toMatchObject({ kind: 'error' })
    expect(parseExternal([EXE, 'content-studio://job/0'])).toMatchObject({ kind: 'error' })
  })

  it('AC-3: WHEN se abre new/narration con text y voice THEN pide rellenar Narración', () => {
    expect(parseExternal([EXE, 'content-studio://new/narration?text=Hola&voice=yesid'])).toEqual({
      kind: 'new',
      type: 'narration',
      params: { text: 'Hola', voice: 'yesid' },
    })
  })

  it('AC-3: WHEN new/media.convert trae input con espacios THEN la ruta llega decodificada', () => {
    expect(parseExternal([EXE, 'content-studio://new/media.convert?input=C%3A%5Cmis%20audios%5Ca.wav&target=mp3'])).toEqual({
      kind: 'new',
      type: 'media.convert',
      params: { input: 'C:\\mis audios\\a.wav', target: 'mp3' },
    })
  })

  it('las secciones que open acepta son las del menú', () => {
    expect([...OPEN_SECTIONS].sort()).toEqual(navItems().map((item) => item.id).sort())
  })
})
