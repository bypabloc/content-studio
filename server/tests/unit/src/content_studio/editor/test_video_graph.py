"""Composición pura de capas en el grafo de FFmpeg."""

from pathlib import Path

from content_studio.editor import project, video_graph


def test_empty_project_builds_the_background_canvas(tmp_path: Path):
    doc = {'canvas': project.DEFAULT_CANVAS, 'tracks': [], 'clips': []}

    plan = video_graph.build(doc, tmp_path)

    assert plan.inputs == []
    assert '[0:v]format=rgba[base]' in plan.script
    assert '[base]null[vout]' in plan.script
