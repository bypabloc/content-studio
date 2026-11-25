import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { UISpeakerLegend } from '@/shared/components/molecules/UISpeakerLegend'
import { t } from '@/shared/i18n/t'

const SPEAKERS = {
  SPEAKER_00: { name: 'Hablante 1', color: '#2563eb' },
  SPEAKER_01: { name: 'Hablante 2', color: '#dc2626' },
}

describe('UISpeakerLegend [AC-5]', () => {
  it('WHEN a name is renamed and the field loses focus THEN onChange gets the whole map with the new name', () => {
    const onChange = vi.fn()
    render(<UISpeakerLegend speakers={SPEAKERS} onChange={onChange} />)
    const field = screen.getByRole('textbox', { name: t('speakers.legend.rename', { name: 'Hablante 1' }) })

    fireEvent.change(field, { target: { value: 'Ana' } })
    fireEvent.blur(field)

    expect(onChange).toHaveBeenCalledWith({ ...SPEAKERS, SPEAKER_00: { name: 'Ana', color: '#2563eb' } })
  })

  it('WHEN the color changes THEN onChange gets the new color at once', () => {
    const onChange = vi.fn()
    render(<UISpeakerLegend speakers={SPEAKERS} onChange={onChange} />)
    const swatch = screen.getByLabelText(t('speakers.legend.color', { name: 'Hablante 2' }))

    fireEvent.change(swatch, { target: { value: '#16a34a' } })

    expect(onChange).toHaveBeenCalledWith({ ...SPEAKERS, SPEAKER_01: { name: 'Hablante 2', color: '#16a34a' } })
  })

  it('WHEN the name is blank THEN it does not save it', () => {
    const onChange = vi.fn()
    render(<UISpeakerLegend speakers={SPEAKERS} onChange={onChange} />)
    const field = screen.getByRole('textbox', { name: t('speakers.legend.rename', { name: 'Hablante 1' }) })

    fireEvent.change(field, { target: { value: '   ' } })
    fireEvent.blur(field)

    expect(onChange).not.toHaveBeenCalled()
  })

  it('WHEN Enter is pressed in the name field THEN it saves the new name', () => {
    const onChange = vi.fn()
    render(<UISpeakerLegend speakers={SPEAKERS} onChange={onChange} />)
    const field = screen.getByRole('textbox', { name: t('speakers.legend.rename', { name: 'Hablante 1' }) })

    fireEvent.change(field, { target: { value: 'Ana' } })
    fireEvent.keyDown(field, { key: 'Enter' })

    expect(onChange).toHaveBeenCalledWith({ ...SPEAKERS, SPEAKER_00: { name: 'Ana', color: '#2563eb' } })
  })

  it('WHEN the name is left unchanged THEN it does not save', () => {
    const onChange = vi.fn()
    render(<UISpeakerLegend speakers={SPEAKERS} onChange={onChange} />)
    const field = screen.getByRole('textbox', { name: t('speakers.legend.rename', { name: 'Hablante 1' }) })

    fireEvent.blur(field)

    expect(onChange).not.toHaveBeenCalled()
  })

  it('WHEN the name is longer than 40 characters THEN it goes back to the saved name', () => {
    const onChange = vi.fn()
    render(<UISpeakerLegend speakers={SPEAKERS} onChange={onChange} />)
    const field = screen.getByRole('textbox', { name: t('speakers.legend.rename', { name: 'Hablante 1' }) })

    fireEvent.change(field, { target: { value: 'x'.repeat(41) } })
    fireEvent.blur(field)

    expect(onChange).not.toHaveBeenCalled()
    expect((field as HTMLInputElement).value).toBe('Hablante 1')
  })

  it('WHEN a speaker has seconds THEN its row shows them and the others show nothing', () => {
    render(<UISpeakerLegend speakers={SPEAKERS} durations={{ SPEAKER_00: 12.34 }} onChange={vi.fn()} />)

    expect(screen.getByText(t('speakers.legend.seconds', { seconds: '12.3' }))).toBeTruthy()
    expect(screen.getByRole('list').querySelectorAll('p')).toHaveLength(1)
  })

  it('WHEN the name changes from outside THEN the field shows the new name', () => {
    const onChange = vi.fn()
    const { rerender } = render(<UISpeakerLegend speakers={SPEAKERS} onChange={onChange} />)

    rerender(<UISpeakerLegend speakers={{ ...SPEAKERS, SPEAKER_00: { name: 'Elena', color: '#2563eb' } }} onChange={onChange} />)

    const field = screen.getByRole('textbox', { name: t('speakers.legend.rename', { name: 'Elena' }) })
    expect((field as HTMLInputElement).value).toBe('Elena')
  })
})
