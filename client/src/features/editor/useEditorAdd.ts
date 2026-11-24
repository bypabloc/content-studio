import { useCallback, useEffect, useState } from 'react';

import { hashParams } from '@/shared/navigation/hash';

function requestedPaths(): string[] {
  return hashParams().getAll('add').filter(Boolean);
}

/** Lee medios añadidos desde otras secciones y los retira del hash al terminar la importación. */
export function useEditorAdd(): { paths: string[]; clear: () => void } {
  const [paths, setPaths] = useState(requestedPaths);

  useEffect(() => {
    const update = () => setPaths(requestedPaths());
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  }, []);

  const clear = useCallback(() => {
    const [section, query = ''] = window.location.hash.split('?', 2);
    const params = new URLSearchParams(query);
    params.delete('add');
    const remaining = params.toString();
    window.location.hash = remaining ? `${section}?${remaining}` : section;
    setPaths([]);
  }, []);

  return { paths, clear };
}
