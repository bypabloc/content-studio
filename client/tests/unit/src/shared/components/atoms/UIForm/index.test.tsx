import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UIForm } from '@/shared/components/atoms/UIForm'

describe('UIForm', () => {
  it('renders an accessible form without native validation', () => {
    render(<UIForm aria-label="Login">x</UIForm>)

    const form = screen.getByRole('form', { name: 'Login' })
    expect(form.hasAttribute('novalidate')).toBe(true)
  })

  it('WHEN the page has not hydrated THEN a native submit posts and never puts fields in the URL', () => {
    render(<UIForm aria-label="Login">x</UIForm>)

    expect(screen.getByRole('form', { name: 'Login' }).getAttribute('method')).toBe('post')
  })

  it('WHEN the action is a function THEN it leaves the method to React', () => {
    render(<UIForm aria-label="Login" action={() => undefined}>x</UIForm>)

    expect(screen.getByRole('form', { name: 'Login' }).hasAttribute('method')).toBe(false)
  })
})
