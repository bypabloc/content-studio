import { openUrl } from '@tauri-apps/plugin-opener';
import { HF_MODEL_URL } from '@/features/engines/HfTokenField';
import { UILink } from '@/shared/components/atoms/UILink';
import { APP_VERSION } from '@/shared/version';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';
import { updateMessage, useUpdater, type UpdaterDeps } from '@/shared/update/useUpdater';

/** Ajustes > Acerca de: la versión, «Buscar actualizaciones» y, si hay una nueva, «Actualizar y reiniciar» (spec 022, D-6). */
export function AboutSettings({ deps }: { deps?: UpdaterDeps }): React.JSX.Element {
  const { state, running, check, install } = useUpdater(deps);
  const message = updateMessage(state, running);
  const busy = state.kind === 'checking' || state.kind === 'waiting' || state.kind === 'installing';

  return (
    <UIStack gap="md">
      <UIText variant="heading">{t('settings.about')}</UIText>
      <UIText variant="body">{t('app.version', { version: APP_VERSION })}</UIText>
      <UIStack gap="xs">
        <UIText variant="caption">{t('settings.about.diarization')}</UIText>
        <UILink
          href={HF_MODEL_URL}
          variant="inline"
          onClick={(event) => {
            event.preventDefault();
            void openUrl(HF_MODEL_URL);
          }}
        >
          {t('settings.about.diarization_link')}
        </UILink>
      </UIStack>
      {message && <UIText variant="caption">{message}</UIText>}
      <UIStack direction="row" gap="sm">
        <UIButton variant="secondary" disabled={busy} onClick={() => void check()}>
          {t('update.check')}
        </UIButton>
        {state.kind === 'available' && <UIButton onClick={install}>{t('update.install')}</UIButton>}
      </UIStack>
    </UIStack>
  );
}
