import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/core';
import { useEffect, useState } from 'react';
import { useApi } from '@/shared/api/context';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UISwitch } from '@/shared/components/atoms/UISwitch';
import { UIText } from '@/shared/components/atoms/UIText';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

/** Lo que devuelve GET y PUT /lan/settings (spec 032, 02 §2). */
interface LanSettings {
  enabled: boolean;
  address: string | null;
  port: number;
  running: boolean;
  url: string | null;
  addresses: string[];
  fingerprint: string | null;
}

interface Device {
  id: number;
  name: string;
}

interface Pin {
  pin: string;
  expires_in: number;
}

const SETTINGS_KEY = ['lan', 'settings'];
const DEVICES_KEY = ['lan', 'devices'];

/**
 * Ajustes > Integraciones > Red local (spec 032, AC-9 y AC-10): activar el acceso desde otros equipos (con la regla del
 * firewall para redes privadas), elegir la dirección, ver la URL y la huella, emparejar con un PIN y revocar
 * dispositivos.
 */
export function LanPanel() {
  const api = useApi();
  const queryClient = useQueryClient();
  const [error, setError] = useState('');
  const [pin, setPin] = useState<{ pin: string; seconds: number } | null>(null);
  const settings = useQuery({ queryKey: SETTINGS_KEY, queryFn: () => api.get<LanSettings>('/lan/settings') });
  // Mientras el PIN está a la vista, la lista se refresca: el dispositivo se empareja desde otro equipo.
  const devices = useQuery({
    queryKey: DEVICES_KEY,
    queryFn: () => api.get<Device[]>('/lan/devices'),
    refetchInterval: pin ? 2000 : false,
  });
  // Solo una respuesta con la forma de /lan/settings: un server viejo o un error no la tienen.
  const current = Array.isArray(settings.data?.addresses) ? settings.data : undefined;
  const list = Array.isArray(devices.data) ? devices.data : [];

  const save = useMutation({
    mutationFn: (changes: Partial<LanSettings>) => api.put<LanSettings>('/lan/settings', changes),
    onSuccess: (data) => queryClient.setQueryData(SETTINGS_KEY, data),
    onError: (failure: Error) => setError(failure.message),
  });

  const revoke = useMutation({
    mutationFn: (id: number) => api.del<void>(`/lan/devices/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: DEVICES_KEY }),
  });

  useEffect(() => {
    if (!pin) return undefined;
    const timer = window.setInterval(() => {
      setPin((shown) => (shown && shown.seconds > 1 ? { ...shown, seconds: shown.seconds - 1 } : null));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [pin !== null]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!current) return null;

  const firewall = async (enabled: boolean): Promise<boolean> => {
    try {
      await invoke('set_lan_firewall', { enabled, port: current.port });
      return true;
    } catch {
      setError(t('settings.lan.firewall_declined'));
      return false;
    }
  };

  const toggle = async (on: boolean) => {
    setError('');
    if (on) {
      if (!(await firewall(true))) return;
      save.mutate({ enabled: true, address: current.address ?? current.addresses[0] });
      return;
    }
    await save.mutateAsync({ enabled: false }).catch(() => undefined);
    await firewall(false);
  };

  const pair = async () => {
    setError('');
    try {
      const created = await api.post<Pin>('/lan/pairing');
      setPin({ pin: created.pin, seconds: created.expires_in });
    } catch (failure) {
      setError((failure as Error).message);
    }
  };

  const options = current.addresses.map((address) => ({ value: address, label: address }));

  return (
    <UIStack gap="md">
      <UIText variant="heading">{t('settings.lan.title')}</UIText>
      <UISwitch
        label={t('settings.lan.enable')}
        description={t('settings.lan.warning')}
        checked={current.enabled}
        onChange={(on) => void toggle(on)}
      />
      {options.length > 0 && (
        <UISelect
          label={t('settings.lan.address')}
          options={options}
          value={current.address ?? ''}
          onChange={(address) => {
            if (address !== current.address) save.mutate({ address });
          }}
        />
      )}
      {current.url && (
        <UIStack gap="xs">
          <UIText variant="caption">{t('settings.lan.url')}</UIText>
          <UIText variant="body">{current.url}</UIText>
        </UIStack>
      )}
      <UIStack gap="xs">
        <UIText variant="caption">{t('settings.lan.fingerprint')}</UIText>
        <UIText variant="body">{current.fingerprint ?? t('settings.lan.fingerprint_pending')}</UIText>
      </UIStack>
      <UIButton variant="secondary" className="self-start" disabled={!current.enabled} onClick={() => void pair()}>
        {t('settings.lan.pair')}
      </UIButton>
      {pin && <UIText variant="body">{t('settings.lan.pin', { pin: pin.pin, seconds: pin.seconds })}</UIText>}
      {error && <UIText variant="caption">{error}</UIText>}
      <UIText variant="caption">{t('settings.lan.devices')}</UIText>
      {devices.isSuccess && list.length === 0 && <UIText variant="caption">{t('settings.lan.no_devices')}</UIText>}
      {list.map((device) => (
        <UIStack key={device.id} gap="xs">
          <UIText variant="body">{device.name}</UIText>
          <UIButton
            variant="danger"
            className="self-start"
            onClick={() => {
              if (window.confirm(t('settings.lan.revoke_confirm', { name: device.name }))) revoke.mutate(device.id);
            }}
          >
            {t('settings.lan.revoke')}
          </UIButton>
        </UIStack>
      ))}
    </UIStack>
  );
}
