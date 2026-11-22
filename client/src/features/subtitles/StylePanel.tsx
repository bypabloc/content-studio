import { useState } from 'react';

import type { StyleIn } from '@/features/subtitles/ass';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UISwitch } from '@/shared/components/atoms/UISwitch';
import { UIField } from '@/shared/components/molecules/UIField';
import { type SelectOption, UIRecommendedSelect } from '@/shared/components/molecules/UIRecommendedSelect';
import { useSetting } from '@/shared/hooks/useSetting';
import { t } from '@/shared/i18n/t';

import { BUILTIN_PRESETS, type PresetName, recommendedPreset } from './presets';

export interface UserPreset {
  name: string;
  style: StyleIn;
}

const OWN = 'own:';

/**
 * El estilo del proyecto: el preset (con ★ según el video), algunos controles y «Guardar como…» (D-9). El último preset
 * usado queda en settings; un preset propio se guarda en `subtitles.presets` y sigue en la lista.
 */
export function StylePanel({
  style,
  aspect,
  onStyleChange,
}: {
  style: StyleIn;
  aspect: number;
  onStyleChange: (next: StyleIn) => void;
}): React.JSX.Element {
  const [userPresets, setUserPresets] = useSetting<UserPreset[]>('subtitles.presets', []);
  const [, setLastPreset] = useSetting<string>('select.subtitles.preset', recommendedPreset(aspect));
  const [draft, setDraft] = useState('');
  const recommended = recommendedPreset(aspect);
  const options: SelectOption[] = [
    { value: 'classic', label: t('subtitles.preset.classic'), recommended: recommended === 'classic' },
    { value: 'reels', label: t('subtitles.preset.reels'), recommended: recommended === 'reels' },
    { value: 'karaoke', label: t('subtitles.preset.karaoke') },
    { value: 'minimal', label: t('subtitles.preset.minimal') },
    ...userPresets.map((preset) => ({ value: `${OWN}${preset.name}`, label: preset.name })),
  ];

  function apply(value: string) {
    const own = userPresets.find((preset) => `${OWN}${preset.name}` === value);
    const next = own ? own.style : BUILTIN_PRESETS[value as PresetName];
    if (next) onStyleChange(next);
  }

  function saveAs() {
    const name = draft.trim();
    if (!name) return;
    setUserPresets([...userPresets.filter((preset) => preset.name !== name), { name, style }]);
    setLastPreset(`${OWN}${name}`);
    setDraft('');
  }

  return (
    <UIStack gap="md">
      <UIRecommendedSelect settingKey="select.subtitles.preset" label={t('subtitles.style.preset')} options={options} onChange={apply} />
      <UISwitch
        label={t('subtitles.style.uppercase')}
        checked={style.uppercase}
        onChange={(checked) => onStyleChange({ ...style, uppercase: checked })}
      />
      <UISwitch label={t('subtitles.style.pop')} checked={style.pop} onChange={(checked) => onStyleChange({ ...style, pop: checked })} />
      <UIField label={t('subtitles.style.presetName')} value={draft} onChange={(event) => setDraft(event.target.value)} />
      <UIButton variant="secondary" onClick={saveAs}>
        {t('subtitles.style.saveAs')}
      </UIButton>
    </UIStack>
  );
}
