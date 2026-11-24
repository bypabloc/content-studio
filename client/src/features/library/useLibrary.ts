import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';

import { useApi } from '@/shared/api/context';

import { libraryQuery } from './query';
import type { Filters, Folder, LibraryResult, Project, Scope, TagCount } from './types';

const RUNNING = ['queued', 'running'];
const STALE_MS = 5 * 60 * 1000; // al abrir, se escanea si el último escaneo tiene más de 5 minutos (D-1)

/** Los ítems de la página con sus filtros; en «Espacio» no pide nada. */
export function useLibraryItems(filters: Filters, scope: Scope, page: number) {
  const api = useApi();
  const query = libraryQuery(filters, scope, page);
  return useQuery({
    queryKey: ['library', 'items', query],
    queryFn: () => api.get<LibraryResult>(`/library?${query}`),
    enabled: scope.type !== 'storage',
  });
}

export function useFolders() {
  const api = useApi();
  return useQuery({ queryKey: ['library', 'folders'], queryFn: () => api.get<Folder[]>('/library/folders') });
}

export function useProjects() {
  const api = useApi();
  return useQuery({ queryKey: ['library', 'projects'], queryFn: () => api.get<Project[]>('/projects') });
}

export function useTags() {
  const api = useApi();
  return useQuery({ queryKey: ['library', 'tags'], queryFn: () => api.get<TagCount[]>('/tags') });
}

/** «Actualizar»: encola `library.scan`, sigue el trabajo y, al terminar, vuelve a pedir la biblioteca. */
export function useScan() {
  const api = useApi();
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState<number | null>(null);
  const scan = useMutation({
    mutationFn: () => api.post<{ id: number }>('/library/scan', {}),
    onSuccess: (job) => setJobId(job.id),
  });
  const job = useQuery({
    queryKey: ['jobs', jobId],
    queryFn: () => api.get<{ status: string }>(`/jobs/${jobId}`),
    enabled: jobId !== null,
    refetchInterval: (query) => (RUNNING.includes(query.state.data?.status ?? 'queued') ? 1000 : false),
  });
  const finished = job.data !== undefined && !RUNNING.includes(job.data.status);
  useEffect(() => {
    if (finished) void queryClient.invalidateQueries({ queryKey: ['library'] });
  }, [finished, queryClient]);
  const { mutate } = scan;
  const refresh = useCallback(() => mutate(), [mutate]);
  return { refresh, scanning: scan.isPending || (jobId !== null && !finished) };
}

/** Al abrir la Biblioteca, un escaneo si el último (`library.last_scan`) tiene más de 5 minutos o no hubo. */
export function useAutoScan(refresh: () => void): void {
  const api = useApi();
  const last = useQuery({
    queryKey: ['settings', 'library.last_scan'],
    queryFn: () => api.get<{ value: string | null }>('/settings/library.last_scan'),
  });
  const asked = useRef(false);
  useEffect(() => {
    if (asked.current || !last.isSuccess) return;
    asked.current = true;
    const value = last.data.value;
    if (!value || Date.now() - Date.parse(value) > STALE_MS) refresh();
  }, [last.isSuccess, last.data, refresh]);
}
