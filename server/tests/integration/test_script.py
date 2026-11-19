"""AC-5: los alias del guion (D-5). `[pause N]` y `"text"` dan los mismos bloques que `[pausa N]` y `"texto"`."""

from __future__ import annotations

from content_studio.narration.script import leer_json
from content_studio.narration.text.segments import segments


def test_ac5_alias_pause_text():
    assert segments('Hola. [pausa 1] Adiós.') == segments('Hola. [pause 1] Adiós.')
    assert leer_json({'texto': ['Uno.', 'Dos.']}) == leer_json({'text': ['Uno.', 'Dos.']})
