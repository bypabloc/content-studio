import { useEffect, useMemo, useRef, useState } from 'react';

import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIPopover } from '@/shared/components/molecules/UIPopover';
import { type SelectOption, UIRecommendedSelect } from '@/shared/components/molecules/UIRecommendedSelect';
import { useRecommendedValue } from '@/shared/hooks/useRecommendedValue';
import { t } from '@/shared/i18n/t';

import {
  advancedFields,
  CHANNEL_OPTIONS,
  type Catalog,
  FORMAT_KEY,
  FPS_OPTIONS,
  formatOptions,
  type FormatChoice,
  PRESET_KEY,
  presetOptions,
  qualityOptions,
  RESOLUTION_OPTIONS,
  rateOptions,
  SOCIAL,
} from './convertOptions';

export type { FormatChoice } from './convertOptions';

type Props = {
  /** Audio si todos los archivos son audio; video si alguno lo es (el audio de un video se extrae). */
  kind: 'audio' | 'video';
  catalog: Catalog;
  /** Recibe la elección efectiva (la guardada o la ★) cada vez que cambia, también al montar. */
  onChange: (choice: FormatChoice) => void;
};

/**
 * Los selectores de Convertir: el formato ★ (con «Redes» como una opción más), la calidad, el preset de red si es
 * «Redes», y «Avanzado» en un popover. Cada selector recuerda su elección; esta pantalla solo informa cuál es.
 *
 * @author Pablo Contreras
 * @since 2026/11/22
 */
export function FormatPicker({ kind, catalog, onChange }: Props): React.JSX.Element {
  const formats = formatOptions(kind, catalog);
  const [format] = useRecommendedValue(FORMAT_KEY, formats);
  const presets = presetOptions(catalog);
  const [preset] = useRecommendedValue(PRESET_KEY, presets);
  const qualities: SelectOption[] = qualityOptions(format);
  const [quality] = useRecommendedValue(`select.convert.quality.${format}`, qualities);
  const rates = rateOptions(format);
  const [channels] = useRecommendedValue('select.convert.channels', CHANNEL_OPTIONS);
  const [rate] = useRecommendedValue('select.convert.rate', rates);
  const [resolution] = useRecommendedValue('select.convert.resolution', RESOLUTION_OPTIONS);
  const [fps] = useRecommendedValue('select.convert.fps', FPS_OPTIONS);

  const choice = useMemo<FormatChoice>(
    () => ({
      format,
      quality,
      preset: format === SOCIAL ? preset : null,
      advanced: { channels, rate, resolution, fps },
    }),
    [format, quality, preset, channels, rate, resolution, fps],
  );
  const report = useRef(onChange);
  useEffect(() => {
    report.current = onChange;
  });
  useEffect(() => {
    report.current(choice);
  }, [choice]);

  const [open, setOpen] = useState(false);
  const anchor = useRef<HTMLButtonElement>(null);
  const fields = advancedFields(format);

  return (
    <UIStack gap="sm">
      <UIRecommendedSelect settingKey={FORMAT_KEY} label={t('convert.format.label')} options={formats} />
      {format === SOCIAL ? (
        <UIRecommendedSelect settingKey={PRESET_KEY} label={t('convert.social.preset')} options={presets} />
      ) : null}
      {qualities.length > 0 ? (
        <UIRecommendedSelect settingKey={`select.convert.quality.${format}`} label={t('convert.quality.label')} options={qualities} />
      ) : null}
      {fields.length > 0 ? (
        <>
          <UIButton ref={anchor} variant="secondary" icon="settings" className="self-start" onClick={() => setOpen((value) => !value)}>
            {t('convert.advanced.label')}
          </UIButton>
          <UIPopover anchor={anchor} open={open} onOpenChange={setOpen} label={t('convert.advanced.label')} align="start">
            <UIStack gap="sm">
              {fields.includes('channels') ? (
                <UIRecommendedSelect settingKey="select.convert.channels" label={t('convert.advanced.channels')} options={CHANNEL_OPTIONS} />
              ) : null}
              {fields.includes('rate') ? (
                <UIRecommendedSelect settingKey="select.convert.rate" label={t('convert.advanced.rate')} options={rates} />
              ) : null}
              {fields.includes('resolution') ? (
                <UIRecommendedSelect settingKey="select.convert.resolution" label={t('convert.advanced.resolution')} options={RESOLUTION_OPTIONS} />
              ) : null}
              {fields.includes('fps') ? (
                <UIRecommendedSelect settingKey="select.convert.fps" label={t('convert.advanced.fps')} options={FPS_OPTIONS} />
              ) : null}
            </UIStack>
          </UIPopover>
        </>
      ) : null}
    </UIStack>
  );
}
