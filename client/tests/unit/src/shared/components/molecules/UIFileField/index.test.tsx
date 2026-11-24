import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { UIFileField } from '@/shared/components/molecules/UIFileField'

describe('UIFileField', () => {
  it('associates the label with the file input and respects accept', () => {
    render(<UIFileField label="Subir firma" accept="image/png,image/jpeg" maxBytesError="Muy grande" chooseLabel="Elegir archivo" emptyLabel="Ningún archivo elegido" />)
    const input = screen.getByLabelText('Subir firma')
    expect(input.getAttribute('type')).toBe('file')
    expect(input.getAttribute('accept')).toBe('image/png,image/jpeg')
  })

  it('WHEN there is an error THEN announces it with aria-describedby and marks the input as invalid', () => {
    render(<UIFileField label="Subir firma" error="Archivo inválido" maxBytesError="Muy grande" chooseLabel="Elegir archivo" emptyLabel="Ningún archivo elegido" />)
    const input = screen.getByLabelText('Subir firma')
    expect(input.getAttribute('aria-invalid')).toBe('true')
    const error = document.getElementById(input.getAttribute('aria-describedby') ?? '')
    expect(error?.textContent).toContain('Archivo inválido')
  })

  it('WHEN the user picks a valid file THEN calls onFile with the file', () => {
    const onFile = vi.fn()
    render(<UIFileField label="Subir firma" onFile={onFile} maxBytesError="Muy grande" chooseLabel="Elegir archivo" emptyLabel="Ningún archivo elegido" />)
    const input = screen.getByLabelText('Subir firma')
    const file = new File(['dummy content'], 'signature.png', { type: 'image/png' })
    fireEvent.change(input, { target: { files: [file] } })
    expect(onFile).toHaveBeenCalledWith(file)
  })

  it('WHEN the file exceeds maxBytes THEN shows a local error and does not call onFile', () => {
    const onFile = vi.fn()
    render(
      <UIFileField
        label="Subir firma"
        maxBytes={100}
        maxBytesError="El archivo supera 100 B"
        chooseLabel="Elegir archivo"
        emptyLabel="Ningún archivo elegido"
        onFile={onFile}
      />,
    )
    const input = screen.getByLabelText('Subir firma')
    const bigFile = new File([new ArrayBuffer(200)], 'heavy.png', { type: 'image/png' })
    fireEvent.change(input, { target: { files: [bigFile] } })
    expect(onFile).not.toHaveBeenCalled()
    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(screen.getByText('El archivo supera 100 B')).toBeTruthy()
  })

  it('WHEN no file is chosen THEN shows its own choose button and the empty text instead of the native one [AC-1.11]', () => {
    render(<UIFileField label="Subir firma" maxBytesError="Muy grande" chooseLabel="Elegir archivo" emptyLabel="Ningún archivo elegido" />)

    expect(screen.getByText('Elegir archivo')).toBeTruthy()
    expect(screen.getByText('Ningún archivo elegido')).toBeTruthy()
    expect(screen.getByLabelText('Subir firma').className).toContain('sr-only')
    expect(screen.getByText('Ningún archivo elegido').className).toContain('min-w-32')
  })

  it('WHEN a valid file is chosen THEN shows its name [AC-1.11]', () => {
    render(<UIFileField label="Subir firma" maxBytesError="Muy grande" chooseLabel="Elegir archivo" emptyLabel="Ningún archivo elegido" />)

    const file = new File(['x'], 'firma.png', { type: 'image/png' })
    fireEvent.change(screen.getByLabelText('Subir firma'), { target: { files: [file] } })

    expect(screen.getByText('firma.png')).toBeTruthy()
    expect(screen.queryByText('Ningún archivo elegido')).toBeNull()
  })
})
