import { act, renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { useForm } from '@/shared/forms/useForm'

type Values = { name: string; items: { code: string }[] }

const INITIAL: Values = { name: '', items: [{ code: 'a' }] }
const validate = (values: Values): Record<string, string> => {
  const errors: Record<string, string> = {}
  if (!values.name) errors.name = 'required'
  values.items.forEach((item, index) => {
    if (!item.code) errors[`items.${index}.code`] = 'required'
  })
  return errors
}

const setup = () => renderHook(() => useForm({ initial: INITIAL, validate }))

describe('useForm [AC-5][AC-6][AC-8][AC-9]', () => {
  it('WHEN no submit happened THEN visibleError returns undefined even if validate fails [AC-5]', () => {
    const { result } = setup()
    expect(result.current.errors.name).toBe('required')
    expect(result.current.visibleError('name')).toBeUndefined()
    expect(result.current.submitCount).toBe(0)
  })

  it('WHEN submit fails THEN submitCount increments, onValid is not called and visibleError returns the error [AC-6]', () => {
    const { result } = setup()
    const onValid = vi.fn()
    let valid = true
    act(() => { valid = result.current.submit(onValid) })
    expect(valid).toBe(false)
    expect(onValid).not.toHaveBeenCalled()
    expect(result.current.submitCount).toBe(1)
    expect(result.current.visibleError('name')).toBe('required')
  })

  it('WHEN a field is fixed after a failed submit THEN its error disappears without resubmitting [AC-6]', () => {
    const { result } = setup()
    act(() => { result.current.submit(vi.fn()) })
    act(() => result.current.set('name', 'Ana'))
    expect(result.current.visibleError('name')).toBeUndefined()
    act(() => result.current.set('items.0.code', ''))
    expect(result.current.visibleError('items.0.code')).toBe('required')
  })

  it('WHEN a value returns to initial THEN dirty and isDirty are false [AC-9]', () => {
    const { result } = setup()
    act(() => result.current.set('name', 'Ana'))
    expect(result.current.dirty('name')).toBe(true)
    expect(result.current.isDirty).toBe(true)
    act(() => result.current.set('name', ''))
    expect(result.current.dirty('name')).toBe(false)
    expect(result.current.isDirty).toBe(false)
  })

  it('WHEN blur is called THEN touched is true for that path only', () => {
    const { result } = setup()
    expect(result.current.touched('name')).toBe(false)
    act(() => result.current.blur('name'))
    expect(result.current.touched('name')).toBe(true)
    expect(result.current.touched('items.0.code')).toBe(false)
  })

  it('WHEN a server error is set and that field changes THEN only that server error is cleared [AC-8]', () => {
    const { result } = setup()
    act(() => { result.current.submit(vi.fn()) })
    act(() => result.current.set('name', 'Ana'))
    act(() => result.current.setServerErrors({ name: 'taken', 'items.0.code': 'document_exists' }))
    expect(result.current.visibleError('name')).toBe('taken')
    act(() => result.current.set('items', [{ code: 'b' }]))
    expect(result.current.visibleError('items.0.code')).toBeUndefined()
    expect(result.current.visibleError('name')).toBe('taken')
  })

  it('WHEN submit passes validation THEN onValid receives the values', () => {
    const { result } = setup()
    const onValid = vi.fn()
    act(() => result.current.set('name', 'Ana'))
    act(() => { result.current.submit(onValid) })
    expect(onValid).toHaveBeenCalledWith({ name: 'Ana', items: [{ code: 'a' }] })
  })

  it('WHEN paths do not exist yet or blur repeats THEN reads are undefined and writes create the branch', () => {
    const { result } = setup()
    expect(result.current.dirty('missing.deep')).toBe(false)
    act(() => result.current.set('extra.value', 'x'))
    expect(result.current.dirty('extra.value')).toBe(true)
    act(() => result.current.blur('name'))
    act(() => result.current.blur('name'))
    expect(result.current.touched('name')).toBe(true)
  })

  it('WHEN setValues and reset are used THEN values update and reset makes the new values pristine', () => {
    const { result } = setup()
    act(() => result.current.setValues((previous) => ({ ...previous, name: 'Luis' })))
    expect(result.current.values.name).toBe('Luis')
    act(() => { result.current.submit(vi.fn()) })
    act(() => result.current.reset({ name: 'Luis', items: [] }))
    expect(result.current.isDirty).toBe(false)
    expect(result.current.submitCount).toBe(0)
    expect(result.current.values.items).toEqual([])
  })
})
