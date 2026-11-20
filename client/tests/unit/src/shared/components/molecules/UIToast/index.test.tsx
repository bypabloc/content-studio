import { act, fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { Toaster } from '@/shared/components/shadcn/sonner'
import { toast, UIToaster } from '@/shared/components/molecules/UIToast'

// El Toaster lee el tema de content-studio, que pide la configuración del server: aquí se fija el tema.
vi.mock('@/shared/theme/useTheme', () => ({ useTheme: () => ['system', vi.fn()] }))

vi.mock('@/shared/components/shadcn/sonner', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/shared/components/shadcn/sonner')>()
  return { Toaster: vi.fn(actual.Toaster) }
})

describe('UIToaster [AC-8]', () => {
  it('WHEN a success or info is notified THEN the message appears in the named region', async () => {
    render(<UIToaster label="Avisos" />)

    act(() => {
      toast.success('Contraseña actualizada')
      toast.info('Sin cambios')
    })

    expect(await screen.findByText('Contraseña actualizada')).toBeTruthy()
    expect(await screen.findByText('Sin cambios')).toBeTruthy()
    expect(screen.getByRole('region', { name: new RegExp('Avisos') })).toBeTruthy()
  })

  it('WHEN an error is notified THEN the message appears and its action button runs the action', async () => {
    const onClick = vi.fn()
    render(<UIToaster label="Avisos" />)

    act(() => {
      toast.error('No se pudo guardar')
      toast.success('Trabajo terminado', { action: { label: 'Abrir carpeta', onClick } })
    })

    expect(await screen.findByText('No se pudo guardar')).toBeTruthy()
    fireEvent.click(await screen.findByRole('button', { name: 'Abrir carpeta' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('WHEN the toaster renders THEN it receives mobileOffset top 5rem [AC-8]', () => {
    render(<UIToaster label="Avisos" />)

    expect(vi.mocked(Toaster).mock.lastCall?.[0]).toMatchObject({
      mobileOffset: { top: '5rem' },
    })
  })
})
