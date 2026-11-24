import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ColorInspector } from '@/features/editor/ColorInspector';
import type { ImageClip } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

const mocks = vi.hoisted(() => ({ api: { upload: vi.fn() }, apiFactory: vi.fn() }));
vi.mock('@/shared/api/context', () => ({ useApi: () => mocks.apiFactory() }));

afterEach(cleanup);
beforeEach(() => {
  vi.clearAllMocks();
  mocks.apiFactory.mockReturnValue(mocks.api);
  mocks.api.upload.mockResolvedValue({ src: 'media/luts/lut-' + 'a'.repeat(64) + '.cube' });
});

const clip: ImageClip = {
  id: 'image-1', track: 'video', src: 'media/image.png', media: 'image', src_in: 0, src_out: 1, start: 0,
  fade_in: 0, fade_out: 0, transform: {
    x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
    crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
  }, keyframes: {},
};

describe('ColorInspector', () => {
  it('muestra los controles de color predeterminados, limita valores y permite quitar LUT', () => {
    const onChange = vi.fn();
    const selected = {
      ...clip,
      color: { brightness: 0, contrast: 1, saturation: 1, gamma: 1, lut: 'media/luts/test.cube' },
    };
    render(<ColorInspector clip={selected} path="/project.json" onChange={onChange} />);

    fireEvent.change(screen.getByLabelText(t('editor.color.brightness')), { target: { value: '2' } });
    expect(onChange).toHaveBeenCalledWith(clip.id, expect.objectContaining({ brightness: 1 }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.color.lut_remove') }));
    expect(onChange).toHaveBeenLastCalledWith(clip.id, {
      brightness: 0, contrast: 1, saturation: 1, gamma: 1,
    });
  });

  it('muestra el error y limpia el campo si falla la subida de LUT', async () => {
    mocks.api.upload.mockRejectedValueOnce(new Error('upload failed'));
    render(<ColorInspector clip={clip} path="/project.json" onChange={vi.fn()} />);
    const input = screen.getByLabelText(t('editor.color.lut')) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(['bad'], 'bad.cube', { type: 'text/plain' })] } });

    expect((await screen.findByRole('alert')).textContent).toBe(t('editor.color.lut_error'));
    await waitFor(() => expect(input.value).toBe(''));
  });

  it('no renderiza controles cuando no hay clip visual', () => {
    const { container } = render(<ColorInspector clip={null} path="/project.json" onChange={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it('uploads a selected cube LUT to the current project and assigns its relative path', async () => {
    const onChange = vi.fn();
    render(<ColorInspector clip={clip} path="D:/project/project.json" onChange={onChange} />);
    const file = new File(['LUT_3D_SIZE 2'], 'identity.cube', { type: 'text/plain' });

    fireEvent.change(screen.getByLabelText(t('editor.color.lut')), { target: { files: [file] } });

    await waitFor(() => expect(mocks.api.upload).toHaveBeenCalledOnce());
    expect(mocks.api.upload).toHaveBeenCalledWith(
      `/editor/projects/luts?path=${encodeURIComponent('D:/project/project.json')}`,
      file,
      'text/plain',
    );
    expect(onChange).toHaveBeenCalledWith(clip.id, expect.objectContaining({ lut: expect.stringContaining('media/luts/lut-') }));
  });
});
