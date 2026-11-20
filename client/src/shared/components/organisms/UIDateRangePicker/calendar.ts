/**
 * Calendario puro del selector de rango: semanas de lunes a domingo, atajos y recorte a límites, sin zona horaria (spec 126, AC-35).
 *
 * @author Pablo Contreras
 * @since 2026/10/31
 */

/** Rango de días en formato `AAAA-MM-DD`; los dos extremos cuentan. */
export type Range = { from: string; to: string }

/** Selección en curso: el inicio y el fin pueden faltar mientras el usuario elige. */
export type Selection = { from: string | null; to: string | null }

/** Atajos del selector, en el orden en que se muestran. */
export type PresetKey = 'today' | 'yesterday' | 'last7' | 'last30' | 'thisMonth' | 'lastMonth'

/** Milisegundos de un día UTC; los días UTC no tienen horario de verano. */
const DAY_MS = 86_400_000

/**
 * Día UTC de un instante en `AAAA-MM-DD`, el mismo día que usa el CUR.
 *
 * @param date - Instante.
 * @returns Fecha ISO del día UTC.
 */
export const toIso = (date: Date): string => date.toISOString().slice(0, 10)

/**
 * Convierte `AAAA-MM-DD` en el día UTC a medianoche.
 *
 * @param iso - Fecha ISO de día.
 * @returns Día UTC a medianoche.
 */
export const fromIso = (iso: string): Date => {
  const [year = 1970, month = 1, day = 1] = iso.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day))
}

/**
 * Desplaza un día tantos días como se pida; los negativos van hacia atrás.
 *
 * @param iso - Día de partida.
 * @param days - Cantidad de días.
 * @returns Día resultante.
 */
export const shiftDay = (iso: string, days: number): string => toIso(new Date(fromIso(iso).getTime() + days * DAY_MS))

/**
 * Primer día (lunes) o último día (domingo) de la semana que contiene el día.
 *
 * @param iso - Día de referencia.
 * @param edge - `start` para el lunes y `end` para el domingo.
 * @returns Día del borde de la semana.
 */
export const weekEdge = (iso: string, edge: 'start' | 'end'): string => {
  const weekday = (fromIso(iso).getUTCDay() + 6) % 7
  return shiftDay(iso, edge === 'start' ? -weekday : 6 - weekday)
}

/**
 * Primer día del mes que contiene el día, desplazado tantos meses como se pida.
 *
 * @param iso - Día de referencia.
 * @param months - Meses a desplazar; negativos hacia atrás.
 * @returns Primer día del mes resultante.
 */
export const monthStart = (iso: string, months: number): string => {
  const date = fromIso(iso)
  return toIso(new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + months, 1)))
}

/**
 * Seis semanas de lunes a domingo que cubren un mes; incluye los días de los meses vecinos.
 *
 * @param year - Año completo.
 * @param month - Mes desde 0 (enero) hasta 11 (diciembre).
 * @returns Seis filas de siete fechas ISO.
 */
export const monthMatrix = (year: number, month: number): string[][] => {
  const offset = (new Date(Date.UTC(year, month, 1)).getUTCDay() + 6) % 7
  const first = Date.UTC(year, month, 1 - offset)
  return Array.from({ length: 6 }, (_, week) =>
    Array.from({ length: 7 }, (_day, index) => toIso(new Date(first + (week * 7 + index) * DAY_MS))),
  )
}

/**
 * Rango de un atajo relativo a hoy, sin recortar a los límites del calendario.
 *
 * @param key - Atajo elegido.
 * @param today - Día de referencia.
 * @returns Rango del atajo.
 */
export const presetRange = (key: PresetKey, today: Date): Range => {
  const todayIso = toIso(today)
  switch (key) {
    case 'today':
      return { from: todayIso, to: todayIso }
    case 'yesterday': {
      const yesterday = shiftDay(todayIso, -1)
      return { from: yesterday, to: yesterday }
    }
    case 'last7':
      return { from: shiftDay(todayIso, -6), to: todayIso }
    case 'last30':
      return { from: shiftDay(todayIso, -29), to: todayIso }
    case 'thisMonth':
      return { from: monthStart(todayIso, 0), to: todayIso }
    case 'lastMonth':
      return { from: monthStart(todayIso, -1), to: shiftDay(monthStart(todayIso, 0), -1) }
  }
}

const clampDay = (iso: string, min?: string, max?: string): string => {
  if (min !== undefined && iso < min) return min
  if (max !== undefined && iso > max) return max
  return iso
}

/**
 * Recorta cada extremo de un rango a los límites del calendario.
 *
 * @param range - Rango a recortar.
 * @param min - Primer día permitido, si lo hay.
 * @param max - Último día permitido, si lo hay.
 * @returns Rango dentro de los límites.
 */
export const clamp = (range: Range, min?: string, max?: string): Range => ({
  from: clampDay(range.from, min, max),
  to: clampDay(range.to, min, max),
})

/** Rango en orden cronológico, sin importar cuál de los dos días se eligió primero. */
const ordered = (first: string, second: string): Range => (first <= second ? { from: first, to: second } : { from: second, to: first })

/**
 * Siguiente selección tras un clic en un día: el primero fija el inicio y el segundo el fin, invertidos si es anterior.
 *
 * @param selection - Selección actual.
 * @param iso - Día pulsado.
 * @returns Selección tras el clic.
 */
export const pickDay = (selection: Selection, iso: string): Selection => {
  if (selection.from === null || selection.to !== null) return { from: iso, to: null }
  return ordered(selection.from, iso)
}

/**
 * Rango tentativo que se pinta al pasar el cursor mientras falta el fin.
 *
 * @param selection - Selección actual.
 * @param hover - Día bajo el cursor, o `null`.
 * @returns Rango tentativo, o `null` si no aplica.
 */
export const previewRange = (selection: Selection, hover: string | null): Range | null => {
  if (selection.from === null || selection.to !== null || hover === null) return null
  return ordered(selection.from, hover)
}

/**
 * Día de referencia del selector: el inyectado en pruebas o el momento actual.
 *
 * @param today - Día inyectado, si lo hay.
 * @returns El día inyectado o la fecha actual.
 */
export const referenceDay = (today?: Date): Date => today ?? new Date()
