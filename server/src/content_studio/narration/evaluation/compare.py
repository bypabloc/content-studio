"""--evaluate: palabras comparables con lo que transcribe whisper y diferencias que no suenan igual."""

from __future__ import annotations

import difflib
import re
import unicodedata

from content_studio.narration.text.segments import NO_MARKS
from content_studio.narration.text.segments import normalize as normalize_marks

# Nombre de cada letra (sin tildes) -> letra, para que "pe de efe" y "PDF" se comparen igual.
# cspell:disable: nombres de letra en español (datos de la comparación con whisper)
LETTERS = {
    'a': 'a',
    'be': 'b',
    'ce': 'c',
    'de': 'd',
    'e': 'e',
    'efe': 'f',
    'ge': 'g',
    'hache': 'h',
    'i': 'i',
    'jota': 'j',
    'ka': 'k',
    'ele': 'l',
    'eme': 'm',
    'ene': 'n',
    'o': 'o',
    'pe': 'p',
    'cu': 'q',
    'erre': 'r',
    'ese': 's',
    'te': 't',
    'u': 'u',
    've': 'v',
    'uve': 'v',
    'equis': 'x',
    'ye': 'y',
    'zeta': 'z',
}
# cspell:enable
# Nombres de letra que no son palabras comunes: si una racha incluye uno, es una sigla.
LETTERS_CLEAR = set(LETTERS) - {'a', 'de', 'e', 'i', 'o', 'u', 'ye', 'te', 'ese', 've'}
# En inglés los números no se comparan: whisper escribe "7", "seven" o "$7" según le parezca, y no hay normalizador
# de números en inglés. Se quitan de los dos lados, junto con "and" ("one hundred and five") y con las unidades de
# moneda y porcentaje que whisper cambia por símbolo ("$7.20", "5%").
# ponytail: sin num2words; comparar números exigiría convertirlos a dígitos en los dos lados.
NUMBERS_EN = {
    'zero',
    'one',
    'two',
    'three',
    'four',
    'five',
    'six',
    'seven',
    'eight',
    'nine',
    'ten',
    'eleven',
    'twelve',
    'thirteen',
    'fourteen',
    'fifteen',
    'sixteen',
    'seventeen',
    'eighteen',
    'nineteen',
    'twenty',
    'thirty',
    'forty',
    'fifty',
    'sixty',
    'seventy',
    'eighty',
    'ninety',
    'hundred',
    'thousand',
    'million',
    'and',
    'dollar',
    'dollars',
    'cent',
    'cents',
    'percent',
}


def normalize(text: str, language: str = 'es') -> list[str]:
    """Palabras comparables con lo que transcribe whisper: sin tildes, signos ni marcas del guion,
    y con las siglas juntas tanto deletreadas ("pe de efe") como en letras ("P D F"). En inglés no se
    normalizan siglas ni números (ver NUMEROS_EN).

    >>> normalize('Sale en pe de efe, con su código cu erre. [pausa 1]')
    ['sale', 'en', 'pdf', 'con', 'su', 'codigo', 'qr']
    >>> normalize('Criterios A, B, C, D, E. ¿Vídeo?')
    ['criterios', 'abcde', 'video']
    >>> normalize('Te enviamos un video y ese día ve la o eme ese.')
    ['te', 'enviamos', 'un', 'video', 'y', 'ese', 'dia', 've', 'la', 'oms']
    >>> normalize('Son 32 piezas, 7 especialidades y 100 recetas.')
    ['son', 'treinta', 'y', 'dos', 'piezas', 'siete', 'especialidades', 'y', 'cien', 'recetas']
    >>> normalize('Me [risa] reí, [enfasis]sí[/enfasis] [estilo: dramatica]de verdad.')
    ['me', 'rei', 'si', 'de', 'verdad']
    >>> normalize('It costs 7 dollars and twenty cents, [risa] really.', 'en')
    ['it', 'costs', 'really']
    >>> normalize('It cost $7.20 and 5 percent more.', 'en')
    ['it', 'cost', 'more']
    """
    if language == 'en':
        return [
            w for w in re.findall(r'[a-z]+', NO_MARKS.sub(' ', normalize_marks(text)).lower()) if w not in NUMBERS_EN
        ]
    t = unicodedata.normalize('NFD', NO_MARKS.sub(' ', normalize_marks(text)).lower())
    words = re.findall(r'\w+', ''.join(c for c in t if unicodedata.category(c) != 'Mn'))
    out: list[str] = []
    streak: list[str] = []

    def dump() -> None:
        loose = all(len(w) == 1 for w in streak) and any(w not in 'aeiouy' for w in streak)
        if len(streak) >= 2 and (loose or LETTERS_CLEAR.intersection(streak)):
            out.append(''.join(LETTERS.get(w, w) for w in streak))
        else:
            out.extend(streak)
        streak.clear()

    for w in words:
        if w.isdigit():
            dump()
            out.extend(as_words(int(w)).split())
        elif w in LETTERS or len(w) == 1:
            streak.append(w)
        else:
            dump()
            out.append(w)
    dump()
    return out


# cspell:disable: números en español (datos de la comparación con whisper)
UNITS = [
    'cero',
    'uno',
    'dos',
    'tres',
    'cuatro',
    'cinco',
    'seis',
    'siete',
    'ocho',
    'nueve',
    'diez',
    'once',
    'doce',
    'trece',
    'catorce',
    'quince',
    'dieciseis',
    'diecisiete',
    'dieciocho',
    'diecinueve',
    'veinte',
    'veintiuno',
    'veintidos',
    'veintitres',
    'veinticuatro',
    'veinticinco',
    'veintiseis',
    'veintisiete',
    'veintiocho',
    'veintinueve',
]
TENS = {3: 'treinta', 4: 'cuarenta', 5: 'cincuenta', 6: 'sesenta', 7: 'setenta', 8: 'ochenta', 9: 'noventa'}
# cspell:enable


# cspell:ignore cien: 100 en español, dato de la comparación (no es un identificador)
def as_words(n: int) -> str:
    """Número de 0 a 100 en palabras, sin tildes (whisper escribe "24" aunque se diga "veinticuatro").

    >>> as_words(7), as_words(24), as_words(32), as_words(40), as_words(2026)
    ('siete', 'veinticuatro', 'treinta y dos', 'cuarenta', '2026')
    """
    if n < 30:
        return UNITS[n]
    if n < 100:
        d, u = divmod(n, 10)
        return TENS[d] + (f' y {UNITS[u]}' if u else '')
    return 'cien' if n == 100 else str(n)


def phonetics(word: str) -> str:
    """Clave de cómo suena una palabra en español latinoamericano (seseo, yeísmo, b = v, h muda).

    >>> [phonetics(w) for w in ('click', 'stock', 'whatsapp', 'zoom', 'clinicae', 'clinicay', 'corriges')]
    ['clic', 'estoc', 'guasap', 'sum', 'clinicai', 'clinicai', 'corrijes']
    >>> phonetics('cuenta') == phonetics('cuento')
    False
    """
    w = word
    for a, b in (
        ('wh', 'gu'),
        ('w', 'gu'),
        ('ck', 'c'),
        ('k', 'c'),
        ('q', 'c'),
        ('z', 's'),
        ('ce', 'se'),
        ('ci', 'si'),
        ('ge', 'je'),
        ('gi', 'ji'),
        ('ll', 'y'),
        ('v', 'b'),
        ('h', ''),
        ('oo', 'u'),
        ('ts', 's'),
    ):
        w = w.replace(a, b)
    w = re.sub(r'([^r])\1', r'\1', w)  # rr suena distinto de r
    w = re.sub(r'^s(?=[ptc])', 'es', w)
    return re.sub(r'(ae|y)$', lambda m: 'ai' if m[1] == 'ae' else 'i', w)


def compare(expected: list[str], hearing: list[str]) -> list[tuple[str, str, str]]:
    """Diferencias (tipo, esperado, oído) entre dos listas de palabras.

    >>> compare(normalize('Cada segundo cuenta.'), normalize('Cada segundo cuento.'))
    [('change', 'cuenta', 'cuento')]
    >>> compare(['hola', 'mundo'], ['hola', 'mundo', 'braids'])
    [('extra', '', 'braids')]
    >>> compare(['hola', 'mundo'], ['mundo'])
    [('missing', 'hola', '')]

    Lo que suena igual no es un error: whisper escribe a su manera las palabras adaptadas.

    >>> compare(['clic', 'en', 'estok', 'por', 'guasap', 'no', 'zum'],
    ...          ['click', 'en', 'stock', 'por', 'whatsapp', 'no', 'zoom'])
    []
    >>> compare(['de', 'pendiente', 'en', 'clinikai'], ['dependiente', 'en', 'clinica', 'y'])
    []
    """
    kinds = {'replace': 'change', 'delete': 'missing', 'insert': 'extra'}
    return [
        (kinds[op], ' '.join(expected[a1:a2]), ' '.join(hearing[b1:b2]))
        for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, expected, hearing, autojunk=False).get_opcodes()
        if op != 'equal' and phonetics(''.join(expected[a1:a2])) != phonetics(''.join(hearing[b1:b2]))
    ]
