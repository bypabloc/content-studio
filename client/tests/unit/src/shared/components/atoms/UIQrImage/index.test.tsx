import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIQrImage } from '@/shared/components/atoms/UIQrImage'

describe('UIQrImage [AC-30]', () => {
  it('WHEN rendered THEN shows the image with its data source and its alt text [AC-30]', () => {
    render(<UIQrImage src="data:image/png;base64,iVBORw0KGgo=" alt="Medical authentication QR code" />)

    const image = screen.getByRole('img', { name: 'Medical authentication QR code' })
    expect(image.getAttribute('src')).toBe('data:image/png;base64,iVBORw0KGgo=')
  })
})
