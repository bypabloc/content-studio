import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { useApi } from '@/shared/api/context';
import { UIMedia } from '@/shared/components/atoms/UIMedia';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIText } from '@/shared/components/atoms/UIText';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIIconButton } from '@/shared/components/molecules/UIIconButton';
import { UISearchField } from '@/shared/components/molecules/UISearchField';
import { UISelect } from '@/shared/components/molecules/UISelect';
import { t } from '@/shared/i18n/t';

import { useNativeDrop } from '../useNativeDrop';
import { FolderTree } from './FolderTree';
import type { BrowserRoot } from './FolderTree';

type Entry = { name: string; path: string; kind: 'folder' | 'audio' | 'video' | 'image'; size?: number; modified?: number };
type Listed = { path: string; entries: Entry[] };
type Filter = 'all' | 'audio' | 'video' | 'image';

const FILTERS = [
  { value: 'all', label: t('editor.browser.kind_all') },
  { value: 'audio', label: t('convert.group.audio') },
  { value: 'video', label: t('convert.group.video') },
  { value: 'image', label: t('editor.browser.kind_image') },
];

function parentPath(path: string): string {
  const clean = path.replace(/[\\/]+$/, '');
  const at = Math.max(clean.lastIndexOf('\\'), clean.lastIndexOf('/'));
  if (at < 0) return path;
  if (/^[A-Za-z]:$/.test(clean.slice(0, at))) return `${clean.slice(0, at + 1)}\\`;
  return clean.slice(0, at) || clean[0] || path;
}

function pathParts(path: string): Array<{ name: string; path: string }> {
  const separator = path.includes('\\') ? '\\' : '/';
  const parts = path.split(/[\\/]/).filter(Boolean);
  let current = path.startsWith('/') ? '/' : '';
  return parts.map((name, index) => {
    current = index === 0 ? `${name}${name.endsWith(':') ? separator : ''}` : `${current}${separator}${name}`;
    return { name, path: current };
  });
}

/** Navega, filtra, muestra una vista previa e importa archivos sin escribir en las carpetas de origen. */
export function FileBrowser({ onImport }: { onImport: (paths: string[]) => void }): React.JSX.Element {
  const api = useApi();
  const [roots, setRoots] = useState<BrowserRoot[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [path, setPath] = useState('');
  const [entries, setEntries] = useState<Entry[]>([]);
  const [filter, setFilter] = useState<Filter>('all');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [previewPath, setPreviewPath] = useState('');
  const [error, setError] = useState(false);
  const mediaRef = useRef<HTMLMediaElement | null>(null);
  const { dragging, pick } = useNativeDrop(onImport);

  useEffect(() => {
    let active = true;
    void Promise.all([
      api.get<{ roots: BrowserRoot[] }>('/fs/roots'),
      api.get<{ value: string[] | null }>('/settings/editor.favorites'),
    ])
      .then(([found, saved]) => {
        if (!active) return;
        const rootsWithFavorites = [...found.roots];
        for (const favorite of saved.value ?? []) {
          if (!rootsWithFavorites.some((root) => root.path === favorite)) {
            rootsWithFavorites.push({ name: favorite.split(/[\\/]/).filter(Boolean).at(-1) ?? favorite, path: favorite });
          }
        }
        setRoots(rootsWithFavorites);
        setFavorites(saved.value ?? []);
        setPath(found.roots[0]?.path ?? '');
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [api]);

  useEffect(() => {
    if (!path) return;
    let active = true;
    const query = new URLSearchParams({ path, kinds: 'audio,video,image' });
    void api
      .get<Listed>(`/fs/list?${query}`)
      .then((result) => {
        if (active) {
          setEntries(result.entries);
          setError(false);
          setSelected([]);
        }
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [api, path]);

  useEffect(() => {
    if (!previewPath || !mediaRef.current) return;
    mediaRef.current.currentTime = 0;
    void mediaRef.current.play().catch(() => undefined);
  }, [previewPath]);

  const visible = useMemo(
    () =>
      entries.filter(
        (entry) =>
          (entry.kind === 'folder' || filter === 'all' || entry.kind === filter) &&
          entry.name.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()),
      ),
    [entries, filter, search],
  );
  const currentName = roots.find((root) => root.path === path)?.name ?? pathParts(path).at(-1)?.name ?? path;
  const favoriteLabel = favorites.includes(path)
    ? t('editor.browser.unfavorite', { name: currentName })
    : t('editor.browser.favorite', { name: currentName });
  const toggleFavorite = useCallback(async () => {
    const next = favorites.includes(path) ? favorites.filter((item) => item !== path) : [...favorites, path];
    setFavorites(next);
    try {
      await api.put('/settings/editor.favorites', { value: next });
      const found = await api.get<{ roots: BrowserRoot[] }>('/fs/roots');
      setRoots(found.roots);
    } catch {
      setFavorites(favorites);
      setError(true);
    }
  }, [api, favorites, path]);

  const preview = useCallback((source: string) => {
    setPreviewPath(source);
    if (mediaRef.current && previewPath === source) void mediaRef.current.play().catch(() => undefined);
  }, [previewPath]);

  function onFileKeyDown(event: React.KeyboardEvent<HTMLButtonElement>, entry: Entry): void {
    if (event.key !== ' ') return;
    event.preventDefault();
    if (entry.kind === 'audio') preview(entry.path);
  }

  return (
    <UIStack role="region" aria-label={t('editor.browser.label')} className={`min-w-64 ${dragging ? 'border border-primary' : ''}`} gap="sm">
      <UIStack direction="row" align="center" justify="between" gap="xs">
        <UIText variant="heading">{t('editor.browser.label')}</UIText>
        <UIStack direction="row" align="center" gap="xs">
          <UIIconButton
            icon="star"
            label={favoriteLabel}
            pressed={favorites.includes(path)}
            disabled={!path}
            onClick={() => void toggleFavorite()}
          />
          <UIButton variant="secondary" icon="open-folder" onClick={() => void pick()}>
            {t('action.import')}
          </UIButton>
        </UIStack>
      </UIStack>
      {error ? <UIText variant="caption">{t('editor.browser.load_error')}</UIText> : null}
      <UIStack direction="row" align="start" gap="sm">
        <FolderTree roots={roots} currentPath={path} onSelect={setPath} />
        <UIStack className="min-w-0 flex-1" gap="sm">
          <UIStack role="navigation" aria-label={t('editor.browser.breadcrumb')} direction="row" align="center" gap="xs">
            {pathParts(path).map((part) => (
              <UIButton key={part.path} variant="ghost" onClick={() => setPath(part.path)}>
                {part.name}
              </UIButton>
            ))}
            <UIIconButton icon="chevron-left" label={t('editor.browser.up')} disabled={!path || parentPath(path) === path} onClick={() => setPath(parentPath(path))} />
          </UIStack>
          <UIStack direction="row" align="end" gap="sm">
            <UISearchField label={t('editor.browser.search')} value={search} onChange={setSearch} />
            <UISelect
              label={t('editor.browser.kind')}
              value={filter}
              options={FILTERS}
              onChange={(value) => setFilter(value as Filter)}
            />
          </UIStack>
          <UIStack role="list" aria-label={t('editor.browser.files')} gap="xs">
            {visible.map((entry) => {
              const isSelected = selected.includes(entry.path);
              return (
                <UIStack key={entry.path} role="listitem" direction="row" align="center" gap="xs">
                  <UIButton
                    variant={isSelected ? 'secondary' : 'ghost'}
                    icon={entry.kind === 'folder' ? 'open-folder' : entry.kind === 'audio' ? 'music' : 'import-file'}
                    block
                    draggable={entry.kind !== 'folder'}
                    onClick={(event) => {
                      if (entry.kind === 'folder') setPath(entry.path);
                      else setSelected(event.ctrlKey || event.metaKey ? (isSelected ? selected.filter((item) => item !== entry.path) : [...selected, entry.path]) : [entry.path]);
                    }}
                    onDoubleClick={() => entry.kind === 'audio' && preview(entry.path)}
                    onMouseEnter={() => entry.kind === 'audio' && preview(entry.path)}
                    onMouseLeave={() => mediaRef.current?.pause()}
                    onKeyDown={(event) => onFileKeyDown(event, entry)}
                    onDragStart={(event) => {
                      const paths = isSelected ? selected : [entry.path];
                      event.dataTransfer.setData('application/x-content-studio-paths', JSON.stringify(paths));
                    }}
                  >
                    {entry.name}
                  </UIButton>
                </UIStack>
              );
            })}
            {visible.length === 0 ? <UIText variant="caption">{t('editor.browser.empty')}</UIText> : null}
          </UIStack>
        </UIStack>
      </UIStack>
      {previewPath ? (
        <UIMedia kind="audio" src={api.queryUrl('/fs/media', { path: previewPath })} mediaRef={(element) => (mediaRef.current = element)} />
      ) : null}
    </UIStack>
  );
}
