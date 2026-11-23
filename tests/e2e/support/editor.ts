import { expect, type Page } from '@playwright/test';

import { apiFixture, openApp, type Call, type Replies } from './app';

type Project = { path: string; hash: string; doc: Record<string, unknown>; missing?: string[] };
export type EditorState = { project: Project; missingRender?: boolean; jobs: number };

export function editorState(missing = false): EditorState {
  return {
    project: apiFixture<Project>(missing ? 'editor/project-missing' : 'editor/project'),
    missingRender: missing,
    jobs: 20,
  };
}

export function editorReplies(state: EditorState): Replies {
  return ({ method, path, search, body }) => {
    if (method === 'GET' && path === '/editor/projects/recent') return apiFixture('editor/recent');
    if (method === 'GET' && path === '/editor/projects') return state.project;
    if (method === 'PUT' && path === '/editor/projects') {
      state.project.doc = structuredClone(body as Record<string, unknown>);
      return apiFixture('editor/saved');
    }
    if (method === 'GET' && path === '/fs/roots') return apiFixture('fs/roots');
    if (method === 'GET' && path === '/fs/list') {
      return search.includes('/exports') ? { path: 'D:/out/editor/demo/exports', entries: [] } : apiFixture('fs/list-media');
    }
    if (method === 'GET' && path === '/fs/info') return apiFixture('fs/info');
    if (method === 'GET' && path.startsWith('/jobs/')) {
      const id = Number(path.slice('/jobs/'.length));
      return { ...apiFixture(state.missingRender ? 'editor/render-missing' : 'editor/render-queued'), id };
    }
    if (method === 'POST' && path === '/jobs') {
      state.jobs += 1;
      return { ...apiFixture('editor/render-queued'), id: state.jobs, params: body };
    }
    return undefined;
  };
}

export function requestBodies(calls: Call[], path: string, method: string): unknown[] {
  return calls.filter((call) => call.method === method && call.path === path).map((call) => call.body);
}

export async function openEditor(page: Page, state: EditorState): Promise<Call[]> {
  const { calls } = await openApp(page, { replies: editorReplies(state) });
  await page.getByRole('navigation').getByRole('link', { name: 'Editor' }).click();
  await page.getByRole('button', { name: 'Abrir demo' }).click();
  await expect(page.getByRole('region', { name: 'Proyecto demo' })).toBeVisible();
  return calls;
}
