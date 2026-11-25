import { useMutation, useQueryClient } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import type { SpeakerMap } from '@/shared/components/molecules/UISpeakerLegend';

/**
 * Guarda los nombres y colores de los hablantes de un trabajo (PUT /jobs/{id}/speakers). Al terminar, la transcripción y
 * los hablantes se vuelven a leer, para que el texto muestre los nombres nuevos.
 */
export function useSaveSpeakers(jobId: number) {
  const api = useApi();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (next: SpeakerMap) => api.put<SpeakerMap>(`/jobs/${jobId}/speakers`, next),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['transcript', jobId] });
      void queryClient.invalidateQueries({ queryKey: ['speakers', jobId] });
    },
  });
}
