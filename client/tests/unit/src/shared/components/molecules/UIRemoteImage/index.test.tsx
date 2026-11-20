import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { UIRemoteImage } from '@/shared/components/molecules/UIRemoteImage'

describe('UIRemoteImage', () => {
  it('renders the image with required alt, width and height and shows a skeleton while loading', () => {
    render(
      <UIRemoteImage
        src="https://example.com/signature.png"
        alt="Firma del doctor"
        width={200}
        height={100}
        errorText="No se pudo cargar la imagen"
        retryLabel="Reintentar carga"
      />,
    )
    const img = screen.getByAltText('Firma del doctor')
    expect(img).toBeTruthy()
    expect(img.getAttribute('width')).toBe('200')
    expect(img.getAttribute('height')).toBe('100')
    expect(screen.getByTestId('remote-image-skeleton')).toBeTruthy()

    fireEvent.load(img)
    expect(screen.queryByTestId('remote-image-skeleton')).toBeNull()
  })

  it('WHEN loading fails THEN shows an error message and a retry button', () => {
    const onRetry = vi.fn()
    render(
      <UIRemoteImage
        src="https://example.com/error.png"
        alt="Firma del doctor"
        width={200}
        height={100}
        errorText="No se pudo cargar la imagen"
        retryLabel="Reintentar carga"
        onRetry={onRetry}
      />,
    )
    const img = screen.getByAltText('Firma del doctor')
    fireEvent.error(img)

    expect(screen.getByText('No se pudo cargar la imagen')).toBeTruthy()
    const retryBtn = screen.getByRole('button', { name: 'Reintentar carga' })
    expect(retryBtn).toBeTruthy()

    fireEvent.click(retryBtn)
    expect(onRetry).toHaveBeenCalled()
  })
})
