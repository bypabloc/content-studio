import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIImage } from '@/shared/components/atoms/UIImage'

describe('UIImage', () => {
  it('muestra la imagen con su texto alternativo y sus dimensiones', () => {
    render(<UIImage src="/portada.png" alt="Portada" width={120} height={80} />)

    const image = screen.getByRole('img', { name: 'Portada' })
    expect(image.getAttribute('src')).toBe('/portada.png')
    expect(image.getAttribute('width')).toBe('120')
    expect(image.getAttribute('height')).toBe('80')
  })

  it('aplica la clase que recibe', () => {
    render(<UIImage src="/portada.png" alt="Portada" className="rounded-xl" />)

    expect(screen.getByRole('img', { name: 'Portada' }).classList.contains('rounded-xl')).toBe(true)
  })
})
