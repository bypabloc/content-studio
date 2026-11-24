import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { EditorPage } from '@/features/editor/EditorPage';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), post: vi.fn() } }));

vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@/features/editor/EditorWorkspace', async () => {
  const React = await import('react');
  return {
    EditorWorkspace: ({ pendingAdd, project }: { pendingAdd?: string[]; project: { path: string } }) =>
      React.createElement('output', { 'data-testid': 'workspace' }, `${project.path}|${pendingAdd?.join('|') ?? ''}`),
  };
});

beforeEach(() => {
  window.location.hash = '#/editor?add=D%3A%2Fmedia%2Fvoice.wav&add=D%3A%2Fmedia%2Fclip.mp4';
  api.get.mockResolvedValue({ paths: [] });
  api.post.mockResolvedValue({ path: 'D:/out/editor/new/project.json', hash: 'hash', doc: {}, missing: [] });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.location.hash = '';
});

describe('EditorPage navigation', () => {
  it('creates a project and passes every requested media path to the workspace', async () => {
    render(<EditorPage />);

    const workspace = await screen.findByTestId('workspace');
    expect(workspace.textContent).toBe('D:/out/editor/new/project.json|D:/media/voice.wav|D:/media/clip.mp4');
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/editor/projects', { name: t('editor.project.default_name') }));
  });
});
