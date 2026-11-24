"""Revisar el guion con el LLM, spec 021 AC-4."""

import json

import pytest

from content_studio.llm.tasks import script_review


def _fake(answer):
    """Un modelo falso: anota el pedido y devuelve la respuesta fija."""
    calls = []

    def ask(messages, rule, check=None):
        calls.append(messages)
        return answer

    return ask, calls


def test_ac4_a_revision_that_improves_the_lint_is_accepted():
    """«Tienes 24 horas; es DEMO.» → «Tienes veinticuatro horas. Es demo.»: menos avisos y sin cifras."""
    text = 'Hola, bienvenido.\n\nTienes 24 horas; es DEMO.'
    ask, calls = _fake(
        {
            'paragraphs': [
                {
                    'index': 1,
                    'revised': 'Tienes veinticuatro horas. Es demo.',
                    'changes': [{'rule': 13, 'before': '24', 'after': 'veinticuatro'}],
                }
            ]
        }
    )

    result = script_review.run({'text': text}, ask)

    assert result['discarded'] == []
    [paragraph] = result['paragraphs']
    assert paragraph['index'] == 1
    assert paragraph['original'] == 'Tienes 24 horas; es DEMO.'
    assert paragraph['revised'] == 'Tienes veinticuatro horas. Es demo.'
    assert paragraph['issues_before'] == 3
    assert paragraph['issues_after'] == 0
    sent = json.dumps(calls[0], ensure_ascii=False)
    assert 'Tienes 24 horas' in sent
    assert 'Hola, bienvenido' not in sent  # sin avisos y sin «revisar todo», no se manda


def test_ac4_a_revision_with_another_idea_is_discarded():
    """Si cambian las palabras de contenido más de un 30 %, el párrafo se descarta con el motivo."""
    ask, _ = _fake(
        {'paragraphs': [{'index': 0, 'revised': 'Compra hoy mismo nuestro producto premium.', 'changes': []}]}
    )

    result = script_review.run({'text': 'Tienes 24 horas; es DEMO.'}, ask)

    assert result['paragraphs'] == []
    assert result['discarded'][0]['index'] == 0
    assert 'content words' in result['discarded'][0]['reasons'][0]


@pytest.mark.parametrize(
    ('revised', 'reason'),
    [
        ('Tienes 24 horas. Es demo.', 'digits'),
        ('Tienes veinticuatro horas; es DEMO; ya', 'lint'),
    ],
)
def test_ac4_digits_or_a_worse_lint_are_discarded(revised, reason):
    """Quedan cifras (regla 13) o el linter da más avisos que antes: se descarta."""
    ask, _ = _fake({'paragraphs': [{'index': 0, 'revised': revised, 'changes': []}]})

    result = script_review.run({'text': 'Tienes 24 horas; es DEMO.'}, ask)

    assert result['paragraphs'] == []
    assert any(reason in item for item in result['discarded'][0]['reasons'])


def test_review_all_sends_every_paragraph_and_ignores_unknown_indexes():
    """Con «revisar todo» van todos los párrafos; un índice que no se pidió o un texto igual no cuentan."""
    ask, calls = _fake(
        {
            'paragraphs': [
                {'index': 0, 'revised': 'Hola, bienvenido.', 'changes': []},
                {'index': 7, 'revised': 'Otro.', 'changes': []},
            ]
        }
    )

    result = script_review.run({'text': 'Hola, bienvenido.\n\nTodo en orden.', 'all': True}, ask)

    assert result == {'paragraphs': [], 'discarded': []}
    assert 'Todo en orden' in json.dumps(calls[0], ensure_ascii=False)


def test_a_clean_script_does_not_call_the_model():
    """Sin avisos y sin «revisar todo», no hay nada que pedirle al modelo."""
    ask, calls = _fake({'paragraphs': []})

    assert script_review.run({'text': 'Todo en orden.'}, ask) == {'paragraphs': [], 'discarded': []}
    assert calls == []


def test_validate_requires_a_text():
    """El trabajo necesita un guion de texto."""
    assert script_review.validate({'text': ''})[0]['code'] == 'invalid_text'
    assert script_review.validate({'text': 'Hola.'}) == []


def test_a_revision_that_removes_accents_is_discarded():
    """Spec 023: Qwen3.5-9B devolvió «como» y «aplicacion» por «cómo» y «aplicación». La regla 12 pide las tildes
    (sin ellas el motor cambia la sílaba tónica): el párrafo se descarta y el motivo nombra las palabras."""
    text = 'Hoy te muestro cómo armo un video, sin salir de una aplicación.'
    revised = 'Hoy te muestro como armo un video, sin salir de una aplicacion.'
    ask, _ = _fake({'paragraphs': [{'index': 0, 'revised': revised, 'changes': []}]})

    result = script_review.run({'text': text, 'all': True}, ask)

    assert result['paragraphs'] == []
    [discarded] = result['discarded']
    assert discarded['reasons'] == ['accents removed: aplicación, cómo']


def test_adding_an_accent_or_keeping_them_is_not_a_removal():
    """Poner una tilde que faltaba («asi» → «así») o dejar las que había no cuenta como quitar tildes."""
    assert script_review.lost_accents('Así ahorro tiempo despues.', 'Así ahorro tiempo después.') == []
    assert script_review.lost_accents('asi ahorro', 'así ahorro') == []
    assert script_review.lost_accents('Una canción', 'Una cancion nueva') == ['canción']
