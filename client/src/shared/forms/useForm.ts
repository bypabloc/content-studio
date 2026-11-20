import { useRef, useState } from 'react'

/** Errores por ruta con punto (`documents.1.number`) → código de error. */
export type FormErrors = Record<string, string>

type Options<T> = {
  initial: T
  validate: (values: T) => FormErrors
}

/** Estado y acciones del formulario que devuelve {@link useForm}. */
export type Form<T> = {
  values: T
  errors: FormErrors
  submitCount: number
  isDirty: boolean
  set: (path: string, value: unknown) => void
  setValues: (update: (previous: T) => T) => void
  blur: (path: string) => void
  touched: (path: string) => boolean
  dirty: (path: string) => boolean
  visibleError: (path: string) => string | undefined
  setServerErrors: (errors: FormErrors) => void
  submit: (onValid: (values: T) => void) => boolean
  reset: (next: T) => void
}

function read(source: unknown, path: string): unknown {
  return path.split('.').reduce<unknown>(
    (current, key) => (current !== null && typeof current === 'object' ? (current as Record<string, unknown>)[key] : undefined),
    source,
  )
}

function write<T>(source: T, path: string, value: unknown): T {
  const [key, ...rest] = path.split('.')
  const container = (source ?? {}) as Record<string, unknown>
  const next = rest.length ? write(container[key!], rest.join('.'), value) : value
  if (Array.isArray(container)) return container.map((item, index) => (String(index) === key ? next : item)) as T
  return { ...container, [key!]: next } as T
}

const same = (a: unknown, b: unknown): boolean => JSON.stringify(a) === JSON.stringify(b)

/**
 * Formulario controlado con validación al envío: `errors` se recalcula en
 * cada render con `validate`, pero `visibleError` solo lo muestra después del
 * primer envío (`submitCount > 0`); desde ahí cada cambio revalida en vivo.
 * `dirty` compara con los valores iniciales y `touched` se marca con `blur`.
 * Los errores del server (`setServerErrors`) se borran al cambiar su campo.
 *
 * @author Pablo Contreras
 * @since 2026/10/30
 */
export function useForm<T>({ initial, validate }: Options<T>): Form<T> {
  const [initialValues, setInitialValues] = useState(initial)
  const [values, setValuesState] = useState(initial)
  const [touchedPaths, setTouchedPaths] = useState<ReadonlySet<string>>(new Set())
  const [submitCount, setSubmitCount] = useState(0)
  const [serverErrors, setServerErrorsState] = useState<FormErrors>({})
  const latest = useRef(values)
  const errors = { ...serverErrors, ...validate(values) }

  const apply = (next: T): void => {
    const previous = latest.current
    latest.current = next
    setValuesState(next)
    setServerErrorsState((current) => Object.fromEntries(
      Object.entries(current).filter(([path]) => same(read(previous, path), read(next, path))),
    ))
  }

  return {
    values,
    errors,
    submitCount,
    isDirty: !same(values, initialValues),
    set: (path, value) => apply(write(latest.current, path, value)),
    setValues: (update) => apply(update(latest.current)),
    blur: (path) => setTouchedPaths((current) => (current.has(path) ? current : new Set(current).add(path))),
    touched: (path) => touchedPaths.has(path),
    dirty: (path) => !same(read(values, path), read(initialValues, path)),
    visibleError: (path) => (submitCount > 0 ? errors[path] : undefined),
    setServerErrors: setServerErrorsState,
    submit: (onValid) => {
      setSubmitCount((count) => count + 1)
      if (Object.keys(validate(latest.current)).length) return false
      onValid(latest.current)
      return true
    },
    reset: (next) => {
      latest.current = next
      setInitialValues(next)
      setValuesState(next)
      setTouchedPaths(new Set())
      setSubmitCount(0)
      setServerErrorsState({})
    },
  }
}
