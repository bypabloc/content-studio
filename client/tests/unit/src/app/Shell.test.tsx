import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { Providers } from '@/app/Providers'
import { Shell } from '@/app/Shell'
import { ApiProvider } from '@/shared/api/context'
import { t } from '@/shared/i18n/t'

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' }

function reply(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200 })
}

/** El server simulado: guarda las preferencias que llegan con PUT y responde colas vacías. */
function server(settings: Record<string, unknown>) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    const marker = '/settings/'
    if (url.includes(marker)) {
      const key = decodeURIComponent(url.slice(url.indexOf(marker) + marker.length))
      if (init?.method === 'PUT') {
        const { value } = JSON.parse(String(init.body)) as { value: unknown }
        settings[key] = value
        return reply({ key, value })
      }
      return reply({ key, value: settings[key] ?? null })
    }
    if (url.endsWith('/engines')) return reply(settings.mockEngines ?? [])
    if (url.endsWith('/voices/catalog')) return reply({ voices: [] })
    if (url.endsWith('/system')) return reply(settings.mockSystem ?? { ffmpeg: { path: 'ffmpeg.exe', version: '9.1' }, git: null, gpu: null })
    if (url.endsWith('/storage')) return reply(settings.mockStorage ?? {
      engines: 'C:/Studio/engines', outputs: 'C:/Studio/outputs',
      engines_used_bytes: 0, engines_free_bytes: 10, outputs_used_bytes: 0, outputs_free_bytes: 10,
    })
    if (url.endsWith('/jobs')) return reply([])
    if (url.endsWith('/subtitles')) return reply([])
    if (url.endsWith('/editor/projects/recent')) return reply({ paths: [] })
    if (url.includes('/catalog/media')) return reply({ formats: [{ id: 'mp3', kind: 'audio' }], presets: [] })
    if (url.includes('kind=media.')) return reply([])
    if (url.includes('/voices/kit')) return reply({ styles: [] })
    if (url.includes('/voices/profiles')) return reply([])
    return reply({ paused: false })
  })
}

function renderShell(settings: Record<string, unknown> = {}) {
  const fetchMock = server({ 'welcome.done': true, ...settings })
  vi.stubGlobal('fetch', fetchMock)
  render(
    <Providers>
      <ApiProvider connection={connection}>
        <Shell version="0.1.0" />
      </ApiProvider>
    </Providers>,
  )
  return fetchMock
}

// Sin globals de vitest, RTL no limpia el DOM entre tests.
afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  window.location.hash = ''
})

describe('Shell [AC-7]', () => {
  it('WHEN la app abre THEN la barra trae las secciones, el botón de tema y la versión al pie', async () => {
    renderShell({ 'ui.theme': 'dark' })

    expect(await screen.findByRole('link', { name: t('nav.narration') })).toBeTruthy()
    expect(screen.getByRole('link', { name: t('nav.settings') })).toBeTruthy()
    expect(
      await screen.findByRole('button', { name: t('theme.change', { mode: t('theme.dark'), next: t('theme.system') }) }),
    ).toBeTruthy()
    expect(screen.getByText(t('app.version', { version: '0.1.0' }))).toBeTruthy()
  })

  it('WHEN ui.sidebar.collapsed está guardado THEN la barra arranca en íconos', async () => {
    renderShell({ 'ui.sidebar.collapsed': true })

    await waitFor(() => expect(document.querySelector('[data-collapsible="icon"]')).not.toBeNull())
  })

  it('WHEN se pulsa el botón de la barra THEN se colapsa y la preferencia se guarda en el server', async () => {
    const user = userEvent.setup()
    const fetchMock = renderShell()

    await user.click(await screen.findByRole('button', { name: t('shell.toggle') }))

    expect(document.querySelector('[data-collapsible="icon"]')).not.toBeNull()
    const saved = fetchMock.mock.calls.find(
      ([url, init]) => String(url).endsWith('/settings/ui.sidebar.collapsed') && init?.method === 'PUT',
    )
    expect(saved).toBeDefined()
    expect(JSON.parse(String(saved?.[1]?.body))).toEqual({ value: true })
  })

  it('Ctrl+K abre la paleta de secciones', async () => {
    renderShell()
    await screen.findByRole('link', { name: t('nav.settings') })

    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })

    expect(screen.getByRole('dialog', { name: t('palette.title') })).toBeTruthy()
  })

  it('Enter en la paleta lleva a la sección elegida', async () => {
    renderShell()
    await screen.findByRole('link', { name: t('nav.settings') })
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })

    const input = screen.getByRole('combobox')
    fireEvent.change(input, { target: { value: 'ajus' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(window.location.hash).toBe('#/settings')
  })

  it('spec 011 (D-6): WHEN se abre Música THEN la sección muestra la duración y los estilos', async () => {
    window.location.hash = '#/music'
    renderShell()

    expect(await screen.findByText(t('music.duration.label'))).toBeTruthy()
  })

  it('spec 009 (AC-7): WHEN se abre Motores THEN muestra la lista instalada', async () => {
    window.location.hash = '#/engines'
    renderShell()

    expect(await screen.findByRole('heading', { level: 1, name: t('engines.title') })).toBeTruthy()
  })

  it('WHEN se abre el catálogo THEN muestra sus opciones de construcción', async () => {
    window.location.hash = '#/catalog'
    renderShell()

    expect(await screen.findByText(t('voices.catalog.intro'))).toBeTruthy()
  })

  it('WHEN se abre Ajustes THEN carga la configuración y el almacenamiento', async () => {
    window.location.hash = '#/settings'
    renderShell()

    expect(await screen.findByText(t('settings.appearance'))).toBeTruthy()
    expect(await screen.findByText(t('storage.title'))).toBeTruthy()
  })

  it('spec 010 (D-6): WHEN se abre Mis voces THEN la sección lista los perfiles', async () => {
    window.location.hash = '#/voices'
    renderShell()

    expect(await screen.findByText(t('voices.empty'))).toBeTruthy()
  })

  it('spec 014: WHEN se abre Subtítulos THEN la sección muestra su lista de proyectos', async () => {
    window.location.hash = '#/subtitles'
    renderShell()

    expect(await screen.findByText(t('subtitles.home.empty'))).toBeTruthy()
  })

  it('spec 017: WHEN se abre el Editor THEN permite crear un proyecto', async () => {
    window.location.hash = '#/editor'
    renderShell()

    expect(await screen.findByRole('button', { name: t('editor.project.create') })).toBeTruthy()
  })

  it('AC-8: el primer uso sin motores abre bienvenida, la completa y va a Narración', async () => {
    const user = userEvent.setup()
    const fetchMock = renderShell({
      'welcome.done': false,
      mockEngines: [],
      mockSystem: { ffmpeg: null, git: null, gpu: null },
    })

    expect(await screen.findByRole('dialog', { name: t('welcome.title') })).toBeTruthy()
    await user.click(screen.getByRole('button', { name: t('welcome.next') }))
    await user.click(screen.getByRole('button', { name: t('welcome.next') }))
    await user.click(screen.getByRole('button', { name: t('welcome.next') }))
    await user.click(screen.getByRole('button', { name: t('welcome.install_continue') }))

    await waitFor(() => expect(fetchMock.mock.calls.some(
      ([url, init]) => String(url).endsWith('/settings/welcome.done') && init?.method === 'PUT' && init.body === JSON.stringify({ value: true }),
    )).toBe(true))
    expect(window.location.hash).toBe('#/narration')
  })

  it('spec 015: WHEN se abre Convertir THEN muestra el botón de convertir', async () => {
    window.location.hash = '#/convert'
    renderShell()

    expect(await screen.findByRole('button', { name: t('convert.submit') })).toBeTruthy()
  })

  it('spec 015: WHEN se abre Normalizar THEN muestra el botón de normalizar', async () => {
    window.location.hash = '#/normalize'
    renderShell()

    expect(await screen.findByRole('button', { name: t('normalize.submit') })).toBeTruthy()
  })
})
