import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';

// Todo lo de voces vive bajo esta clave: un cambio de perfil refresca la lista, la ficha y el progreso.
const VOICES = ['voices'];

/** Un estilo de la ficha de un perfil: si tiene referencia elegida, su archivo y cuántas tomas hay. */
export interface StyleStatus {
  style: string;
  chosen: boolean;
  takes: number;
  reference: string | null;
}

/** Un perfil de la lista: los estilos que ya tienen referencia elegida (`GET /voices/profiles`). */
export interface ProfileSummary {
  id: string;
  name: string;
  styles: string[];
}

/** Un perfil con todos los estilos del kit (`GET /voices/profiles/{slug}`). */
export interface ProfileDetail {
  id: string;
  name: string;
  styles: StyleStatus[];
}

/**
 * Un estilo del kit (`GET /voices/kit`): su guion marcado y el exacto, la duración objetivo, el ritmo (`null` si no tiene)
 * y si es opcional (el susurro queda fuera del progreso).
 */
export interface KitStyle {
  style: string;
  optional: boolean;
  text: string;
  marked: string;
  duration: { min: number; max: number };
  ppm: number | null;
}

/** Los estilos de grabación en orden de sesión. No cambian durante la vida de la app: se piden una vez. */
export function useKit() {
  const api = useApi();
  return useQuery({
    queryKey: [...VOICES, 'kit'],
    queryFn: () => api.get<{ styles: KitStyle[] }>('/voices/kit'),
    staleTime: Infinity,
  });
}

/** La lista de perfiles con los estilos que ya tienen referencia. */
export function useProfiles() {
  const api = useApi();
  return useQuery({
    queryKey: [...VOICES, 'profiles'],
    queryFn: () => api.get<ProfileSummary[]>('/voices/profiles'),
  });
}

/** Un perfil con sus estilos. */
export function useProfile(slug: string) {
  const api = useApi();
  return useQuery({
    queryKey: [...VOICES, 'profile', slug],
    queryFn: () => api.get<ProfileDetail>(`/voices/profiles/${encodeURIComponent(slug)}`),
  });
}

/** Crear, renombrar y borrar perfiles. Borrar siempre va con `confirm=true`: el server lo manda a la papelera. */
export function useProfileMutations() {
  const api = useApi();
  const queryClient = useQueryClient();
  const refresh = () => queryClient.invalidateQueries({ queryKey: VOICES });
  return {
    create: useMutation({
      mutationFn: (name: string) => api.post<{ id: string; name: string }>('/voices/profiles', { name }),
      onSuccess: refresh,
    }),
    rename: useMutation({
      mutationFn: ({ id, name }: { id: string; name: string }) =>
        api.patch(`/voices/profiles/${encodeURIComponent(id)}`, { name }),
      onSuccess: refresh,
    }),
    remove: useMutation({
      mutationFn: (id: string) => api.del(`/voices/profiles/${encodeURIComponent(id)}?confirm=true`),
      onSuccess: refresh,
    }),
  };
}
