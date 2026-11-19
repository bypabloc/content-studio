import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';

type SettingOut = components['schemas']['SettingOut'];

/**
 * Una preferencia de la tabla settings. Mientras llega (o si nunca se guardó), vale `fallback`. Al cambiarla,
 * la caché cambia enseguida y después se hace el PUT.
 */
export function useSetting<T>(key: string, fallback: T): [T, (value: T) => void] {
  const api = useApi();
  const queryClient = useQueryClient();
  const path = `/settings/${encodeURIComponent(key)}`;
  const query = useQuery({
    queryKey: ['settings', key],
    queryFn: () => api.get<SettingOut>(path),
  });
  const save = useMutation({
    mutationFn: (value: T) => api.put<SettingOut>(path, { value }),
    onSuccess: (saved) => queryClient.setQueryData(['settings', key], saved),
  });
  const stored = query.data?.value;
  const set = (value: T) => {
    queryClient.setQueryData<SettingOut>(['settings', key], { key, value });
    save.mutate(value);
  };
  return [(stored ?? fallback) as T, set];
}
