import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ICON_NAMES, UIIcon } from '@/shared/components/atoms/UIIcon'

describe('UIIcon', () => {
  it('WHEN without label THEN it is decorative and hidden from screen readers', () => {
    const { container } = render(<UIIcon name="user" />)

    const svg = container.querySelector('svg')
    expect(svg?.getAttribute('aria-hidden')).toBe('true')
    expect(svg?.getAttribute('class')).toContain('size-5')
  })

  it('WHEN with label THEN exposed as an image with an accessible name', () => {
    render(<UIIcon name="eye" label="Logo" className="size-8" />)

    expect(screen.getByRole('img', { name: 'Logo' }).getAttribute('class')).toContain('size-8')
  })

  it('WHEN an icon is requested THEN renders the matching lucide-react path', () => {
    const { container } = render(<UIIcon name="bell" />)

    expect(container.querySelector('svg')?.getAttribute('class')).toContain('lucide-bell')
  })

  it('WHEN each name of the set is requested THEN all exist in lucide', () => {
    for (const name of ICON_NAMES) {
      const { container, unmount } = render(<UIIcon name={name} />)
      expect(container.querySelector('svg'), name).not.toBeNull()
      unmount()
    }
  })

  it('WHEN the charge icon is requested THEN it renders the wallet path [AC-9]', () => {
    const { container } = render(<UIIcon name="wallet" />)

    expect(container.querySelector('svg')?.getAttribute('class')).toContain('lucide-wallet')
  })

  it('WHEN the charge icon is requested THEN it renders the banknote path [AC-44]', () => {
    expect(ICON_NAMES).toContain('banknote')
    const { container } = render(<UIIcon name="banknote" />)

    expect(container.querySelector('svg')?.getAttribute('class')).toContain('lucide-banknote')
  })

  it('WHEN the development settings icon is requested THEN it renders the settings path [AC-11]', () => {
    expect(ICON_NAMES).toContain('settings')
    const { container } = render(<UIIcon name="settings" />)

    expect(container.querySelector('svg')?.getAttribute('class')).toContain('lucide-settings')
  })

  it('WHEN the appointment and patient creation icons are requested THEN they exist in lucide', () => {
    for (const name of ['calendar-plus', 'user-plus'] as const) {
      expect(ICON_NAMES).toContain(name)
      const { container, unmount } = render(<UIIcon name={name} />)
      expect(container.querySelector('svg')?.getAttribute('class')).toContain(`lucide-${name}`)
      unmount()
    }
  })

  it('WHEN the WhatsApp, FAQ assistant and close icons are requested THEN they render their lucide paths', () => {
    for (const name of ['message-circle', 'bot', 'x', 'bug'] as const) {
      expect(ICON_NAMES).toContain(name)
      const { container, unmount } = render(<UIIcon name={name} />)
      expect(container.querySelector('svg')?.getAttribute('class')).toContain(`lucide-${name}`)
      unmount()
    }
  })

  it('WHEN the operations console icons are requested THEN they render their lucide paths', () => {
    const paths = [
      ['calendar-range', 'lucide-calendar-range'],
      ['receipt', 'lucide-receipt'],
      ['circle-help', 'lucide-circle-question-mark'],
      ['circle-user', 'lucide-circle-user'],
      ['power', 'lucide-power'],
      ['power-off', 'lucide-power-off'],
      ['database', 'lucide-database'],
      ['server', 'lucide-server'],
      ['loader-circle', 'lucide-loader-circle'],
      ['history', 'lucide-rotate-ccw-clock'],
    ] as const
    for (const [name, lucideClass] of paths) {
      expect(ICON_NAMES).toContain(name)
      const { container, unmount } = render(<UIIcon name={name} />)
      expect(container.querySelector('svg')?.getAttribute('class')).toContain(lucideClass)
      unmount()
    }
  })
})

describe('UIIcon: íconos del shell (spec 008, D-3)', () => {
  it('trae los que pide el shell: tema, sidebar y cola', () => {
    for (const name of ['sun', 'moon', 'monitor', 'panel-left-close', 'panel-left-open', 'list-ordered']) {
      expect(ICON_NAMES).toContain(name);
    }
  });

  it('no trae los iconos de la clínica', () => {
    expect(ICON_NAMES).not.toContain('stethoscope');
    expect(ICON_NAMES).not.toContain('tooth');
  });
});

