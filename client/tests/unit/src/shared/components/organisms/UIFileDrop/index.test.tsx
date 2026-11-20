import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { UIFileDrop } from '@/shared/components/organisms/UIFileDrop'

const PROPS = {
  label: 'Attachments',
  chooseLabel: 'Choose files',
  dropLabel: 'or drop them here',
  accept: 'application/pdf,image/png,.docx',
  maxBytes: 100,
}

function file(name: string, type: string, size = 10): File {
  return new File([new ArrayBuffer(size)], name, { type })
}

function zone(): HTMLElement {
  return screen.getByRole('button', { name: /Choose files/ })
}

describe('UIFileDrop', () => {
  it('WHEN files are dropped THEN onFiles receives the accepted ones [AC-5]', () => {
    const onFiles = vi.fn()
    render(<UIFileDrop {...PROPS} onFiles={onFiles} />)
    const pdf = file('a.pdf', 'application/pdf')
    const docx = file('b.docx', '')

    fireEvent.drop(zone(), { dataTransfer: { files: [pdf, docx] } })

    expect(onFiles).toHaveBeenCalledWith([pdf, docx], [])
  })

  it('WHEN a file exceeds maxBytes or the accept list THEN it is reported as rejected and not passed [AC-5]', () => {
    const onFiles = vi.fn()
    render(<UIFileDrop {...PROPS} onFiles={onFiles} />)
    const ok = file('ok.png', 'image/png')
    const big = file('big.pdf', 'application/pdf', 200)
    const exe = file('x.exe', 'application/octet-stream')

    fireEvent.change(screen.getByLabelText('Attachments'), { target: { files: [ok, big, exe] } })

    expect(onFiles).toHaveBeenCalledWith(
      [ok],
      [
        { file: big, reason: 'too_large' },
        { file: exe, reason: 'type_not_allowed' },
      ],
    )
  })

  it('WHEN the zone is focused and Enter is pressed THEN the input opens (click on input) [AC-5]', () => {
    render(<UIFileDrop {...PROPS} onFiles={vi.fn()} />)
    const click = vi.spyOn(screen.getByLabelText('Attachments'), 'click')

    fireEvent.keyDown(zone(), { key: 'Enter' })
    fireEvent.keyDown(zone(), { key: ' ' })
    fireEvent.keyDown(zone(), { key: 'a' })

    expect(click).toHaveBeenCalledTimes(2)
  })

  it('WHEN dragover THEN the zone is highlighted (data-dragging) [AC-5]', () => {
    render(<UIFileDrop {...PROPS} onFiles={vi.fn()} />)

    fireEvent.dragOver(zone())
    expect(zone().dataset.dragging).toBe('true')

    fireEvent.dragLeave(zone())
    expect(zone().dataset.dragging).toBeUndefined()
  })

  it('WHEN disabled THEN dropping or pressing Enter does nothing', () => {
    const onFiles = vi.fn()
    render(<UIFileDrop {...PROPS} disabled onFiles={onFiles} />)
    const click = vi.spyOn(screen.getByLabelText('Attachments'), 'click')

    fireEvent.drop(zone(), { dataTransfer: { files: [file('a.pdf', 'application/pdf')] } })
    fireEvent.keyDown(zone(), { key: 'Enter' })

    expect(onFiles).not.toHaveBeenCalled()
    expect(click).not.toHaveBeenCalled()
    expect(zone().getAttribute('aria-disabled')).toBe('true')
  })

  it('WHEN no accept or maxBytes THEN every file passes and the hint is described', () => {
    const onFiles = vi.fn()
    render(<UIFileDrop label="Attachments" chooseLabel="Choose files" dropLabel="or drop them" hint="Up to 25 MB" onFiles={onFiles} />)
    const any = file('x.bin', '', 10_000)

    fireEvent.change(screen.getByLabelText('Attachments'), { target: { files: [any] } })

    expect(onFiles).toHaveBeenCalledWith([any], [])
    const hintId = zone().getAttribute('aria-describedby') ?? ''
    expect(document.getElementById(hintId)?.textContent).toBe('Up to 25 MB')
  })

  it('WHEN the input change has no files THEN onFiles is not called', () => {
    const onFiles = vi.fn()
    render(<UIFileDrop {...PROPS} onFiles={onFiles} />)

    fireEvent.change(screen.getByLabelText('Attachments'), { target: { files: [] } })

    expect(onFiles).not.toHaveBeenCalled()
  })
})
