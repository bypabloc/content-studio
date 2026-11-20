import { useState } from 'react';
import { RecordWizard } from '@/features/recording/RecordWizard';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIGrid } from '@/shared/components/atoms/UIGrid';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIEmpty } from '@/shared/components/molecules/UIEmpty';
import { UIConfirmDialog } from '@/shared/components/organisms/UIConfirmDialog';
import { t } from '@/shared/i18n/t';
import { ProfileCard } from './ProfileCard';
import { ProfileDetail } from './ProfileDetail';
import { ProfileNameDialog } from './ProfileNameDialog';
import { type ProfileSummary, useKit, useProfileMutations, useProfiles } from './useVoices';

// Lo que tiene abierto el diálogo de perfiles: crear uno nuevo, o renombrar o borrar uno de la lista.
type VoiceDialog = { kind: 'new' } | { kind: 'rename'; profile: ProfileSummary } | { kind: 'remove'; profile: ProfileSummary };

/**
 * La sección Mis voces (spec 010, D-6): cada perfil con su progreso sobre los 12 estilos obligatorios, y crear, renombrar
 * y borrar (a la papelera, con confirmación). Abrir un perfil muestra su ficha; «Volver» regresa a la lista.
 */
export function MyVoicesPage() {
  const profiles = useProfiles();
  const kit = useKit();
  const { create, rename, remove } = useProfileMutations();
  const [opened, setOpened] = useState<string | null>(null);
  const [recording, setRecording] = useState<string | null>(null);
  const [dialog, setDialog] = useState<VoiceDialog | null>(null);
  const [draft, setDraft] = useState('');

  // El asistente reemplaza la ficha mientras se graba; al terminar (o «Volver») regresa a la ficha del mismo perfil.
  if (recording !== null) return <RecordWizard slug={recording} onDone={() => setRecording(null)} />;
  if (opened !== null) {
    return <ProfileDetail slug={opened} onBack={() => setOpened(null)} onRecord={() => setRecording(opened)} />;
  }

  const required = (kit.data?.styles ?? []).filter((item) => !item.optional).map((item) => item.style);
  const renaming = dialog?.kind === 'rename';
  const failure = renaming ? rename.error : create.error;
  const openNew = () => {
    create.reset();
    setDraft('');
    setDialog({ kind: 'new' });
  };
  const openRename = (profile: ProfileSummary) => {
    rename.reset();
    setDraft(profile.name);
    setDialog({ kind: 'rename', profile });
  };
  const submitName = () => {
    const name = draft.trim();
    if (dialog?.kind === 'new') create.mutate(name, { onSuccess: () => setDialog(null) });
    if (dialog?.kind === 'rename') rename.mutate({ id: dialog.profile.id, name }, { onSuccess: () => setDialog(null) });
  };
  const closeDialog = (open: boolean) => {
    if (!open) setDialog(null);
  };

  return (
    <UIStack gap="lg">
      <UIButton icon="plus" className="self-start" onClick={openNew}>
        {t('voices.new')}
      </UIButton>
      {profiles.isSuccess && profiles.data.length === 0 ? <UIEmpty icon="voices" title={t('voices.empty')} /> : null}
      <UIGrid columns={2}>
        {(profiles.data ?? []).map((profile) => (
          <ProfileCard
            key={profile.id}
            profile={profile}
            done={profile.styles.filter((style) => required.includes(style)).length}
            total={required.length}
            onOpen={() => setOpened(profile.id)}
            onRename={() => openRename(profile)}
            onRemove={() => setDialog({ kind: 'remove', profile })}
          />
        ))}
      </UIGrid>
      <ProfileNameDialog
        open={dialog?.kind === 'new' || renaming}
        onOpenChange={closeDialog}
        title={renaming ? t('voices.rename.title') : t('voices.new.title')}
        description={renaming ? t('voices.rename.description') : t('voices.new.description')}
        confirmLabel={renaming ? t('action.save') : t('action.create')}
        value={draft}
        onChange={setDraft}
        pending={create.isPending || rename.isPending}
        error={failure?.message}
        onSubmit={submitName}
      />
      <UIConfirmDialog
        open={dialog?.kind === 'remove'}
        onOpenChange={closeDialog}
        title={t('voices.delete.title', { name: dialog?.kind === 'remove' ? dialog.profile.name : '' })}
        description={t('voices.delete.description')}
        confirmLabel={t('voices.delete.confirm')}
        cancelLabel={t('action.cancel')}
        destructive
        onConfirm={() => {
          if (dialog?.kind === 'remove') remove.mutate(dialog.profile.id);
        }}
      />
    </UIStack>
  );
}
