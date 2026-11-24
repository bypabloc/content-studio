"""Agrupación y grafo de transiciones entre capas visuales."""

from dataclasses import dataclass
from pathlib import Path

from content_studio.editor import video_transitions


@dataclass
class FakeTransform:
    lines: list[str]
    label: str
    x: str = '0'
    y: str = '0'


def test_groups_only_join_adjacent_clips_when_transition_intersects_range():
    items = _items(2)
    transition = _transition('a', 'b')

    active = video_transitions.groups(items, [transition], 2.5, 2.6)
    outside = video_transitions.groups(items, [transition], 1.5, 1.8)

    assert len(active) == 1
    assert [clip['id'] for clip, _ in active[0].items] == ['a', 'b']
    assert active[0].transitions == [transition]
    assert [len(group.items) for group in outside] == [1, 1]


def test_compose_transitions_trims_the_full_chain_to_requested_range(tmp_path: Path):
    items = _items(3)
    transitions = [_transition('a', 'b'), _transition('b', 'c')]
    group = video_transitions.groups(items, transitions, 2.5, 4.5)[0]
    indexes = {(tmp_path / f'{clip["id"]}.png').resolve(): i + 1 for i, (clip, _) in enumerate(items)}
    sizes = {path: (32, 32) for path in indexes}

    layer = video_transitions.compose(
        group,
        tmp_path,
        indexes,
        sizes,
        {'width': 256, 'height': 256, 'fps': 10},
        2.5,
        4.5,
        't0',
        _transform,
    )

    script = ';'.join(layer.lines)
    assert 'xfade=transition=fade:duration=1:offset=2' in script
    assert 'xfade=transition=fade:duration=1:offset=4' in script
    assert 'trim=start=2.5:end=4.5' in script
    assert layer.start == 2.5 and layer.end == 4.5


def test_compose_uses_source_in_for_video_clips(tmp_path: Path):
    items = _items(2, media='video')
    group = video_transitions.groups(items, [_transition('a', 'b')], 2.5, 2.6)[0]
    indexes = {(tmp_path / f'{clip["id"]}.mp4').resolve(): i + 1 for i, (clip, _) in enumerate(items)}
    sizes = {path: (32, 32) for path in indexes}

    layer = video_transitions.compose(
        group,
        tmp_path,
        indexes,
        sizes,
        {'width': 256, 'height': 256, 'fps': 10},
        2.5,
        2.6,
        't1',
        _transform,
    )

    assert '[1:v]trim=start=1:duration=3' in layer.lines[0]


def test_compose_applies_video_speed_before_the_transition(tmp_path: Path):
    """La velocidad cambia los fotogramas de fuente, pero el cruce sigue en tiempo de timeline."""
    items = _items(2, media='video')
    for clip, _ in items:
        clip['speed'] = 2
    items[1][0]['start'] = 0.5
    transition = _transition('a', 'b')
    group = video_transitions.groups(items, [transition], 0, 2)[0]
    indexes = {(tmp_path / f'{clip["id"]}.mp4').resolve(): i + 1 for i, (clip, _) in enumerate(items)}
    sizes = {path: (32, 32) for path in indexes}

    layer = video_transitions.compose(
        group,
        tmp_path,
        indexes,
        sizes,
        {'width': 256, 'height': 256, 'fps': 10},
        0,
        2,
        't2',
        _transform,
    )

    assert sum('trim=start=1:duration=3,setpts=(PTS-STARTPTS)/2' in line for line in layer.lines) == 2
    assert 'xfade=transition=fade:duration=1:offset=0.5' in ';'.join(layer.lines)


def test_compose_rejects_a_group_without_one_transition_per_cut():
    group = video_transitions.Group(_items(2), [])

    try:
        video_transitions.compose(group, Path('.'), {}, {}, {}, 0, 1, 't', _transform)
    except ValueError as error:
        assert str(error) == 'bad_transition_group'
    else:
        raise AssertionError('Se esperaba rechazar el grupo inválido')


def _transform(clip, track, source, start, source_size, namespace):
    label = f'{namespace}transform'
    return FakeTransform([f'[{source}]null[{label}]'], label)


def _items(count: int, media: str = 'image'):
    return [
        (
            {
                'id': chr(ord('a') + index),
                'track': 'v1',
                'src': f'{chr(ord("a") + index)}.{"png" if media == "image" else "mp4"}',
                'media': media,
                'src_in': 1 if media == 'video' else 0,
                'src_out': 4 if media == 'video' else 3,
                'start': index * 2,
            },
            {'id': 'v1', 'kind': 'video', 'opacity': 1},
        )
        for index in range(count)
    ]


def _transition(a: str, b: str):
    return {'id': f'{a}-{b}', 'a': a, 'b': b, 'track': 'v1', 'type': 'fade', 'duration': 1}
