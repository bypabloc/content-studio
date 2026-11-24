import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIBadge } from '@/shared/components/atoms/UIBadge';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIField } from '@/shared/components/molecules/UIField';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { toast } from '@/shared/components/molecules/UIToast';
import { t } from '@/shared/i18n/t';

import type { LibraryItem } from './types';
import { useProjects } from './useLibrary';

/** Etiquetas y proyectos del ítem (D-3): agregar y quitar etiquetas, y sumarlo a un proyecto. */
export function ItemOrganize({ item }: { item: LibraryItem }): React.JSX.Element {
  const api = useApi();
  const queryClient = useQueryClient();
  const projects = useProjects();
  const [tag, setTag] = useState('');
  const list = projects.data ?? [];
  const refresh = () => void queryClient.invalidateQueries({ queryKey: ['library'] });
  const onError = (error: Error) => toast.error(error.message);
  const addTag = useMutation({
    mutationFn: () => api.post(`/library/${item.id}/tags`, { name: tag }),
    onSuccess: () => {
      setTag('');
      refresh();
    },
    onError,
  });
  const removeTag = useMutation({
    mutationFn: (name: string) => api.del(`/library/${item.id}/tags?name=${encodeURIComponent(name)}`),
    onSuccess: refresh,
    onError,
  });
  const addToProject = useMutation({
    mutationFn: (projectId: string) => api.post(`/projects/${projectId}/items`, { items: [item.id] }),
    onSuccess: () => {
      toast.success(t('library.projects.added'));
      refresh();
    },
    onError,
  });
  return (
    <UIStack gap="sm" role="group" aria-label={t('library.organize')}>
      <UIStack direction="row" gap="sm" className="flex-wrap">
        {item.tags.map((name) => (
          <UIStack key={name} direction="row" gap="sm" align="center">
            <UIBadge icon="tag">{name}</UIBadge>
            <UIIconButton icon="remove" label={t('library.tags.remove', { name })} onClick={() => removeTag.mutate(name)} />
          </UIStack>
        ))}
      </UIStack>
      <UIStack direction="row" gap="sm" align="end">
        <UIField label={t('library.tags.new')} value={tag} onChange={(event) => setTag(event.target.value)} />
        <UIButton variant="secondary" icon="tag" disabled={!tag.trim()} onClick={() => addTag.mutate()}>
          {t('library.tags.add')}
        </UIButton>
      </UIStack>
      {list.length > 0 ? (
        <UISelect
          label={t('library.projects.add')}
          value="none"
          options={[
            { value: 'none', label: t('library.projects.choose') },
            ...list.map((project) => ({ value: String(project.id), label: project.name })),
          ]}
          onChange={(value) => (value === 'none' ? undefined : addToProject.mutate(value))}
        />
      ) : null}
    </UIStack>
  );
}
