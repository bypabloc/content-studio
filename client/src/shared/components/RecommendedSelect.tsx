import { useId } from 'react';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

export interface SelectOption {
  value: string;
  label: string;
  recommended?: boolean;
  disabled?: boolean;
  hint?: string;
}

/**
 * Un selector que recuerda la última elección (en settings, con la clave `settingKey`). Sin elección guardada, o si la
 * guardada ya no existe, vale la recomendada, marcada con ★ (AC-3). Con `beforeChange`, la elección solo se aplica
 * si esa función responde que sí (la licencia de un motor, AC-7); si no, el selector sigue en la opción anterior.
 */
export function RecommendedSelect({
  settingKey,
  label,
  options,
  onChange,
  beforeChange,
}: {
  settingKey: string;
  label: string;
  options: readonly SelectOption[];
  onChange?: (value: string) => void;
  beforeChange?: (value: string) => Promise<boolean>;
}) {
  const recommended = options.find((option) => option.recommended)?.value ?? options[0]?.value ?? '';
  const [stored, setStored] = useSetting<string>(settingKey, recommended);
  const value = options.some((option) => option.value === stored) ? stored : recommended;
  const choose = (next: string) => {
    setStored(next);
    onChange?.(next);
  };

  const id = useId();
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(event) => {
          const next = event.target.value;
          if (beforeChange) void beforeChange(next).then((allowed) => allowed && choose(next));
          else choose(next);
        }}
        className="rounded-md border border-input bg-transparent px-2 py-1.5 text-sm"
      >
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
            title={option.recommended ? t('select.recommended') : option.hint}
          >
            {option.recommended ? `★ ${option.label}` : option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
