"""Composición pura de capas en el grafo de FFmpeg."""

from pathlib import Path

from content_studio.editor import project, video_graph


def test_empty_project_builds_the_background_canvas(tmp_path: Path):
    doc = {'canvas': project.DEFAULT_CANVAS, 'tracks': [], 'clips': []}

    plan = video_graph.build(doc, tmp_path)

    assert plan.inputs == []
    assert '[0:v]format=rgba[base]' in plan.script
    assert '[base]null[vout]' in plan.script


def test_text_raster_is_looped_as_a_still_image(tmp_path: Path):
    source = tmp_path / 'media' / 'text-title.png'
    transform = {
        'x': 0,
        'y': 0,
        'scale_x': 1,
        'scale_y': 1,
        'rotation': 0,
        'opacity': 1,
        'anchor_x': 0.5,
        'anchor_y': 0.5,
        'crop': {'l': 0, 't': 0, 'r': 0, 'b': 0},
    }
    doc = {
        'canvas': {**project.DEFAULT_CANVAS, 'width': 320, 'height': 180},
        'tracks': [{'id': 'titles', 'kind': 'video', 'name': 'Títulos', 'opacity': 1, 'hidden': False}],
        'clips': [
            {
                'id': 'title',
                'track': 'titles',
                'src': str(source),
                'src_in': 0,
                'src_out': 2,
                'start': 0,
                'fade_in': 0,
                'fade_out': 0,
                'speed': 1,
                'media': 'text',
                'transform': transform,
                'keyframes': {},
            }
        ],
    }

    plan = video_graph.build(doc, tmp_path, source_sizes={source.resolve(): (320, 90)})

    assert plan.inputs[0].image is True
