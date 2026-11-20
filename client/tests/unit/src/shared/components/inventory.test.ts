import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

// AC-1 (spec 008): el inventario de D-3 más los componentes que llegaron después (los átomos de la gráfica, `UIFieldFrame`,
// `UIQrCode`, `UIDiffText`, `UIImage`, `UITime`…). Cambiar esta lista es decidir que entra o sale un componente.
const INVENTORY = {
  atoms: [
    'UIAvatar', 'UIBadge', 'UIBox', 'UIButton', 'UICard', 'UIChartMarker', 'UIChartPlaceholder', 'UICheckbox',
    'UIDetailText', 'UIDiffText', 'UIFieldError', 'UIFieldFrame', 'UIFixedValue', 'UIForm', 'UIGrid', 'UIHiddenInput',
    'UIIcon', 'UIImage', 'UILink', 'UIMarkedText', 'UIPage', 'UIProgress', 'UIQrCode', 'UIQrImage', 'UIRouteTransition',
    'UISkeleton', 'UIStack', 'UIStatus', 'UIStatusBadge', 'UISwitch', 'UITime', 'UIText', 'UITooltip',
  ],
  molecules: [
    'UIAlert', 'UICheckboxGroup', 'UICollapsible', 'UICombobox', 'UIDateParts', 'UIDateRangeFilter', 'UIDescriptionList',
    'UIEmpty', 'UIErrorSummary', 'UIField', 'UIFileField', 'UIIconButton', 'UIMonthGrid', 'UIPagination', 'UIPasswordField',
    'UIPopover', 'UIRadioGroup', 'UIRecommendedSelect', 'UIRemoteImage', 'UIRowActions', 'UISearchField', 'UISearchSelect',
    'UISelect', 'UIStatCard', 'UIStepProgress', 'UITabs', 'UITextarea', 'UIThemeToggle', 'UITimeline', 'UIToast',
  ],
  organisms: [
    'UIAppShell', 'UIBottomSheet', 'UIChart', 'UIChartCard', 'UICommandPalette', 'UIConfirmDialog', 'UIDateRangePicker',
    'UIDialog', 'UIFileDrop', 'UIFloatingToolbar', 'UIFormDialog', 'UIRepeatGroup', 'UIRowTable', 'UITable',
  ],
} as const

// El componente principal de una carpeta lleva su nombre; `UIToast` es la excepción: su export es `UIToaster`, el
// contenedor de los avisos. La API `toast` vive en el mismo archivo (WARNING 008-inventario-d3).
const MAIN_EXPORT: Record<string, string> = { UIToast: 'UIToaster' }

type Level = keyof typeof INVENTORY

// Vitest corre desde client/: el código está en src/ y su espejo de pruebas, en tests/unit/src/.
const SOURCE = join(process.cwd(), 'src', 'shared', 'components')
const MIRROR = join(process.cwd(), 'tests', 'unit', 'src', 'shared', 'components')

describe('inventario de componentes (AC-1)', () => {
  for (const level of Object.keys(INVENTORY) as Level[]) {
    it(`${level}/ tiene exactamente los componentes del inventario`, () => {
      expect(readdirSync(join(SOURCE, level)).sort()).toEqual([...INVENTORY[level]].sort())
    })

    it(`cada componente de ${level}/ tiene index.tsx, un export UI<Nombre> y su test espejo`, () => {
      for (const name of INVENTORY[level]) {
        const file = join(SOURCE, level, name, 'index.tsx')

        expect(existsSync(file), `${name}: falta index.tsx`).toBe(true)
        const exported = MAIN_EXPORT[name] ?? name
        expect(readFileSync(file, 'utf8'), `${name}: falta el export ${exported}`).toMatch(
          new RegExp(`export (function|const) ${exported}\\b`),
        )
        expect(existsSync(join(MIRROR, level, name, 'index.test.tsx')), `${name}: falta su test espejo`).toBe(true)
      }
    })
  }
})
