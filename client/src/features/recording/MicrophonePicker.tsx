import { useState } from 'react';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';
import { listMicrophones, microphoneOptions } from './microphones';
import type { RecordingLog } from './recordingLog';

/**
 * El micrófono con el que se graba (spec 010, D-2). «Ver micrófonos» lista los de entrada del sistema; el elegido se
 * guarda en ajustes y la grabación y la prueba de sala lo usan. Sin elegir, es el predeterminado de Windows.
 * `log` anota si la lista salió o falló (spec 010, D-7); sin él, no anota nada.
 */
export function MicrophonePicker({
  value,
  onChange,
  disabled = false,
  log,
}: {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  log?: RecordingLog;
}): React.JSX.Element {
  const [devices, setDevices] = useState<MediaDeviceInfo[] | null>(null);
  const [failed, setFailed] = useState(false);

  const show = async () => {
    setFailed(false);
    try {
      const found = await listMicrophones();
      setDevices(found);
      log?.('mic.list', { devices: found.filter((device) => device.kind === 'audioinput').map((device) => device.label) });
    } catch (failure) {
      setFailed(true);
      log?.('mic.list.error', { name: failure instanceof Error ? failure.name : 'unknown' });
    }
  };

  return (
    <UIStack gap="sm">
      <UIButton variant="secondary" disabled={disabled} onClick={() => void show()}>
        {t('voices.mic.show')}
      </UIButton>
      {devices ? (
        <UISelect
          label={t('voices.mic.label')}
          emptyOption={t('voices.mic.default')}
          options={microphoneOptions(devices, (n) => t('voices.mic.unnamed', { n }))}
          value={value}
          onChange={onChange}
          disabled={disabled}
        />
      ) : null}
      {failed ? <UIText variant="caption">{t('voices.mic.error')}</UIText> : null}
    </UIStack>
  );
}
