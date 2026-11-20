import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIQrCode } from '@/shared/components/atoms/UIQrCode'

describe('UIQrCode', () => {
  it('draws the path as an image with an accessible name and a viewBox of the size', () => {
    render(<UIQrCode size={29} stroke="M4 4h2v1h-2z" label="Patient link QR code for Ana" />)
    const img = screen.getByRole('img', { name: 'Patient link QR code for Ana' })
    expect(img.getAttribute('viewBox')).toBe('0 0 29 29')
    expect(img.querySelector('path')?.getAttribute('d')).toBe('M4 4h2v1h-2z')
  })
})
