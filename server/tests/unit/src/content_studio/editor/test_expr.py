"""Expresiones de FFmpeg para las curvas compartidas de keyframes."""

from content_studio.editor import expr


def test_property_expression_is_constant_without_keyframes():
    assert expr.property_expression([], 2, 7) == '7'


def test_property_expression_golden_for_linear_and_hold_segments():
    frames = [
        {'t': 0, 'value': 0, 'ease': 'linear'},
        {'t': 1, 'value': 10, 'ease': 'hold'},
        {'t': 2, 'value': 20, 'ease': 'linear'},
    ]

    assert expr.property_expression(frames, 3, 99) == 'if(lt(t,1),(0+10*((t-0)/1)),if(lt(t,2),10,20))'


def test_property_expression_shifts_clip_local_keyframes_to_the_render_range():
    frames = [{'t': 0, 'value': 0, 'ease': 'linear'}, {'t': 2, 'value': 400, 'ease': 'linear'}]

    assert expr.property_expression(frames, 2, 99, offset=-3) == '(0+400*((t-(-3))/2))'


def test_property_expression_uses_cubic_smoothstep_for_ease_in_out():
    frames = [{'t': 0, 'value': 0, 'ease': 'ease-in-out'}, {'t': 2, 'value': 1, 'ease': 'linear'}]

    assert expr.property_expression(frames, 2, 99) == ('(0+1*(3*((t-0)/2)*((t-0)/2)-2*((t-0)/2)*((t-0)/2)*((t-0)/2)))')
