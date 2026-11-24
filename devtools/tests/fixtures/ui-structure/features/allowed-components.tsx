import { UIStack } from '@/shared/components/atoms/UIStack';

export const identity = <T,>(value: T) => value;

export function Panel() {
  return <UIStack gap="sm">{identity('ok')}</UIStack>;
}
