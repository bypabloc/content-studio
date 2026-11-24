import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIField } from '@/shared/components/molecules/UIField';
import { UIDialog } from '@/shared/components/organisms/UIDialog';
import { useApi } from '@/shared/api/context';
import { t } from '@/shared/i18n/t';

export const parts = [UIStack, UIField, UIDialog, useApi, t];
