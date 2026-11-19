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
 * guardada ya no existe, vale la recomendada, marcada con ★ (AC-3).
 */
export function RecommendedSelect({
  settingKey,
  label,
  options,
  onChange,
}: {
  settingKey: string;
  label: string;
  options: readonly SelectOption[];
  onChange?: (value: string) => void;
}) {
  const recommended = options.find((option) => option.recommended)?.value ?? options[0]?.value ?? '';
  const [stored, setStored] = useSetting<string>(settingKey, recommended);
  const value = options.some((option) => option.value === stored) ? stored : recommended;

  return (
    <select
      aria-label={label}
      value={value}
      onChange={(event) => {
        setStored(event.target.value);
        onChange?.(event.target.value);
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
  );
}
