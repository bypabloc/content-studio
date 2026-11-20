import { cn } from 'cn'
import type { ReactNode } from 'react'

import { UIBox } from '../../atoms/UIBox'
import { UIButton } from '../../atoms/UIButton'

/** Item of a day: a button with its text and an optional badge (for example, a status icon). */
export type MonthDayItem = { id: string; text: string; badge?: ReactNode }
/** Day of the month grid. `outside` marks days of the adjacent months; `more` is the overflow text ("+2 más"). */
export type MonthDay = { date: string; label: string; outside: boolean; today: boolean; items: MonthDayItem[]; more?: string }

type Props = {
  /** Accessible name of the grid. */
  caption: string
  /** Weekday headers, Monday first, already translated. */
  weekdays: string[]
  days: MonthDay[]
  /** Text that marks today for screen readers, next to the visual style ("hoy"). */
  todayText: string
  onDaySelect: (date: string) => void
  onItemSelect: (id: string) => void
}

/** Items shown per day before the `more` text. */
const VISIBLE_ITEMS = 3

/** Splits the days into weeks of seven. */
function weeksOf(days: MonthDay[]): MonthDay[][] {
  return Array.from({ length: Math.ceil(days.length / 7) }, (_, week) => days.slice(week * 7, week * 7 + 7))
}

/** Monday-first index (0 = Monday) of an ISO `YYYY-MM-DD` date, computed in UTC so the browser zone cannot move it. */
function weekdayIndex(date: string): number {
  const [year = 1970, month = 1, day = 1] = date.split('-').map(Number)
  return (new Date(Date.UTC(year, month - 1, day)).getUTCDay() + 6) % 7
}

type DayProps = {
  day: MonthDay
  /** Visible text of the day button: the number, or the weekday and the number in the list. */
  name: string
  todayText: string
  onDaySelect: (date: string) => void
  onItemSelect: (id: string) => void
}

/** Day button with its first items: the button selects the day, each item selects its appointment. */
function DayBody({ day, name, todayText, onDaySelect, onItemSelect }: DayProps): React.JSX.Element {
  return (
    <>
      <UIButton
        variant="ghost"
        block
        onClick={() => onDaySelect(day.date)}
        className="justify-between rounded-lg px-1 text-left text-sm font-bold text-foreground transition-colors duration-200 hover:bg-accent focus-visible:ui-focus motion-reduce:transition-none"
      >
        {name}
        {day.today ? <>{' '}<UIBox as="span" className="sr-only">{todayText}</UIBox></> : null}
      </UIButton>
      <UIBox role="list" className="mt-1 flex flex-col gap-1">
        {day.items.slice(0, VISIBLE_ITEMS).map((item) => (
          <UIBox role="listitem" key={item.id}>
            <UIButton
              variant="ghost"
              block
              onClick={() => onItemSelect(item.id)}
              className="min-w-0 items-center gap-1 rounded-md border border-accent bg-accent px-1.5 py-0.5 text-left text-xs leading-tight text-accent-foreground transition-colors duration-200 hover:border-primary focus-visible:ui-focus motion-reduce:transition-none"
            >
              {item.badge}
              <UIBox as="span" className="truncate">{item.text}</UIBox>
            </UIButton>
          </UIBox>
        ))}
        {day.more ? <UIBox role="listitem" className="px-1 text-xs text-muted-foreground">{day.more}</UIBox> : null}
      </UIBox>
    </>
  )
}

/**
 * Mes en cuadrícula: un `role="grid"` de semanas con un botón por día (su número y
 * "hoy" como texto además del estilo) y hasta tres citas, con el texto "+N más" si
 * hay más. Por debajo de `@3xl` (375 px) la misma información pasa a una lista por
 * día con su día de la semana. Elegir un día llama `onDaySelect` con su fecha ISO;
 * todo el copy llega ya traducido. Sin `table` nativa (spec 008, D-4): filas y
 * celdas son `role="row"` (con `display: contents`) y `role="gridcell"`.
 *
 * @author Pablo Contreras
 * @since 2026/10/11
 * @since 2026/11/19
 */
export function UIMonthGrid({ caption, weekdays, days, todayText, onDaySelect, onItemSelect }: Props): React.JSX.Element {
  return (
    <UIBox className="@container">
      <UIBox role="grid" aria-label={caption} className="hidden w-full grid-cols-7 gap-1 @3xl:grid">
        <UIBox role="row" className="contents">
          {weekdays.map((weekday) => (
            <UIBox role="columnheader" key={weekday} className="pb-1 text-left text-sm font-bold text-foreground-secondary">
              {weekday}
            </UIBox>
          ))}
        </UIBox>
        {weeksOf(days).map((week) => (
          <UIBox role="row" key={week[0]?.date ?? ''} className="contents">
            {week.map((day) => (
              <UIBox
                role="gridcell"
                key={day.date}
                className={cn('rounded-xl border border-border bg-card p-1.5', day.outside && 'bg-muted text-muted-foreground', day.today && 'ring-2 ring-ring')}
              >
                <DayBody day={day} name={day.label} todayText={todayText} onDaySelect={onDaySelect} onItemSelect={onItemSelect} />
              </UIBox>
            ))}
          </UIBox>
        ))}
      </UIBox>
      <UIBox role="list" aria-label={caption} className="flex flex-col gap-2 @3xl:hidden">
        {days.map((day) => (
          <UIBox
            role="listitem"
            key={day.date}
            className={cn('rounded-xl border border-border bg-card p-2', day.outside && 'text-muted-foreground', day.today && 'ring-2 ring-ring')}
          >
            <DayBody
              day={day}
              name={`${weekdays[weekdayIndex(day.date)] ?? ''} ${day.label}`}
              todayText={todayText}
              onDaySelect={onDaySelect}
              onItemSelect={onItemSelect}
            />
          </UIBox>
        ))}
      </UIBox>
    </UIBox>
  )
}
