import { UIRecommendedSelect } from '@/shared/components/molecules/UIRecommendedSelect';
import { useSetting } from '@/shared/hooks/useSetting';

/** Las voces con las favoritas primero; cada grupo conserva el orden en que ya venían (AC-9). */
export function favoritesFirst<T extends { id: string }>(voices: readonly T[], favorites: readonly string[]): T[] {
  return [
    ...voices.filter((voice) => favorites.includes(voice.id)),
    ...voices.filter((voice) => !favorites.includes(voice.id)),
  ];
}

/**
 * El selector de voz de la narración (spec 010, AC-9): recuerda la última elección, como cualquier selector, y pone
 * primero las voces que están en las favoritas de `voices.favorites`.
 */
export function VoiceSelect({
  settingKey,
  label,
  voices,
}: {
  settingKey: string;
  label: string;
  voices: readonly { id: string }[];
}): React.JSX.Element {
  const [favorites] = useSetting<string[]>('voices.favorites', []);
  const options = favoritesFirst(voices, favorites).map((voice) => ({ value: voice.id, label: voice.id }));
  return <UIRecommendedSelect settingKey={settingKey} label={label} options={options} />;
}
