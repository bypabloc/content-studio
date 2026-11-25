import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { UISpeakerCountField } from '@/shared/components/molecules/UISpeakerCountField'
import { t } from '@/shared/i18n/t'

describe('UISpeakerCountField [AC-2]', () => {
  it('WHEN exact is chosen and a number is typed THEN it sends num_speakers', async () => {
    const onChange = vi.fn()
    render(<UISpeakerCountField onChange={onChange} />)

    await userEvent.click(await screen.findByRole('combobox', { name: t('speakers.count.label') }))
    await userEvent.click(await screen.findByRole('option', { name: t('speakers.count.exact') }))
    fireEvent.change(screen.getByRole('spinbutton', { name: t('speakers.count.number') }), { target: { value: '2' } })

    expect(onChange).toHaveBeenLastCalledWith({ num_speakers: 2 })
  })

  it('WHEN a range is chosen THEN it sends min_speakers and max_speakers', async () => {
    const onChange = vi.fn()
    render(<UISpeakerCountField onChange={onChange} />)

    await userEvent.click(await screen.findByRole('combobox', { name: t('speakers.count.label') }))
    await userEvent.click(await screen.findByRole('option', { name: t('speakers.count.range') }))
    fireEvent.change(screen.getByRole('spinbutton', { name: t('speakers.count.min') }), { target: { value: '2' } })
    fireEvent.change(screen.getByRole('spinbutton', { name: t('speakers.count.max') }), { target: { value: '4' } })

    expect(onChange).toHaveBeenLastCalledWith({ min_speakers: 2, max_speakers: 4 })
  })

  it('WHEN automatic is chosen again THEN it sends no count', async () => {
    const onChange = vi.fn()
    render(<UISpeakerCountField onChange={onChange} />)

    await userEvent.click(await screen.findByRole('combobox', { name: t('speakers.count.label') }))
    await userEvent.click(await screen.findByRole('option', { name: t('speakers.count.exact') }))
    fireEvent.change(screen.getByRole('spinbutton', { name: t('speakers.count.number') }), { target: { value: '3' } })
    await userEvent.click(await screen.findByRole('combobox', { name: t('speakers.count.label') }))
    await userEvent.click(await screen.findByRole('option', { name: t('speakers.count.auto') }))

    expect(onChange).toHaveBeenLastCalledWith({})
  })

  it('WHEN the number is outside 1 to 20 THEN it shows the error and does not send it', async () => {
    const onChange = vi.fn()
    render(<UISpeakerCountField onChange={onChange} />)

    await userEvent.click(await screen.findByRole('combobox', { name: t('speakers.count.label') }))
    await userEvent.click(await screen.findByRole('option', { name: t('speakers.count.exact') }))
    fireEvent.change(screen.getByRole('spinbutton', { name: t('speakers.count.number') }), { target: { value: '21' } })

    expect(screen.getByText(t('error.invalid_speakers'))).toBeTruthy()
    expect(onChange).not.toHaveBeenLastCalledWith({ num_speakers: 21 })
  })
})
