import { useQuery } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

export interface JobRow {
  id: number;
  kind: string;
  status: string;
  starred: boolean;
  params: Record<string, unknown>;
  output_dir: string | null;
}

export interface UIJobPickerProps {
  kinds: string[];
  label: string;
  onPick: (job: JobRow) => void;
}

// i18n-ignore: la estrella es un símbolo, no un texto: marca la elección del grupo.
const STAR = '★';

/**
 * Elige un trabajo terminado de esos tipos para una ranura («Del historial», spec 016 D-4). La elección del grupo (★)
 * va primero, y luego el más reciente.
 */
export function UIJobPicker({ kinds, label, onPick }: UIJobPickerProps): React.JSX.Element {
  const api = useApi();
  const jobs = useQuery({ queryKey: ['jobs', 'done'], queryFn: () => api.get<JobRow[]>('/jobs?status=done') });
  const rows = (jobs.data ?? [])
    .filter((job) => job.status === 'done' && kinds.includes(job.kind))
    .sort((a, b) => Number(b.starred) - Number(a.starred) || b.id - a.id);
  const options = rows.map((job) => ({
    value: String(job.id),
    label: `${job.starred ? `${STAR} ` : ''}${job.kind} #${job.id}`,
  }));
  return (
    // Con `emptyOption` el selector siempre se muestra y no elige solo cuando hay un único trabajo; `value` vacío
    // hace que cada elección dispare `onChange`, también la del mismo trabajo otra vez.
    <UISelect
      label={label}
      emptyOption={t('mix.source.pickJob')}
      value=""
      options={options}
      onChange={(value) => {
        const job = rows.find((row) => String(row.id) === value);
        if (job) onPick(job);
      }}
    />
  );
}
