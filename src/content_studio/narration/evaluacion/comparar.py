"""--evaluar: palabras comparables con lo que transcribe whisper y diferencias que no suenan igual."""

from __future__ import annotations

import difflib
import re
import unicodedata

from content_studio.narration.texto.segmentos import SIN_MARCAS

# Nombre de cada letra (sin tildes) -> letra, para que "pe de efe" y "PDF" se comparen igual.
LETRA = {
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
# Nombres de letra que no son palabras comunes: si una racha incluye uno, es una sigla.
LETRA_CLARA = set(LETRA) - {'a', 'de', 'e', 'i', 'o', 'u', 'ye', 'te', 'ese', 've'}
# En inglés los números no se comparan: whisper escribe "7", "seven" o "$7" según le parezca, y no hay normalizador
# de números en inglés. Se quitan de los dos lados, junto con "and" ("one hundred and five") y con las unidades de
# moneda y porcentaje que whisper cambia por símbolo ("$7.20", "5%").
# ponytail: sin num2words; comparar números exigiría convertirlos a dígitos en los dos lados.
NUMEROS_EN = {
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


def normalizar(texto: str, idioma: str = 'es') -> list[str]:
    """Palabras comparables con lo que transcribe whisper: sin tildes, signos ni marcas del guion,
    y con las siglas juntas tanto deletreadas ("pe de efe") como en letras ("P D F"). En inglés no se
    normalizan siglas ni números (ver NUMEROS_EN).

    >>> normalizar('Sale en pe de efe, con su código cu erre. [pausa 1]')
    ['sale', 'en', 'pdf', 'con', 'su', 'codigo', 'qr']
    >>> normalizar('Criterios A, B, C, D, E. ¿Vídeo?')
    ['criterios', 'abcde', 'video']
    >>> normalizar('Te enviamos un video y ese día ve la o eme ese.')
    ['te', 'enviamos', 'un', 'video', 'y', 'ese', 'dia', 've', 'la', 'oms']
    >>> normalizar('Son 32 piezas, 7 especialidades y 100 recetas.')
    ['son', 'treinta', 'y', 'dos', 'piezas', 'siete', 'especialidades', 'y', 'cien', 'recetas']
    >>> normalizar('Me [risa] reí, [enfasis]sí[/enfasis] [estilo: dramatica]de verdad.')
    ['me', 'rei', 'si', 'de', 'verdad']
    >>> normalizar('It costs 7 dollars and twenty cents, [risa] really.', 'en')
    ['it', 'costs', 'really']
    >>> normalizar('It cost $7.20 and 5 percent more.', 'en')
    ['it', 'cost', 'more']
    """
    if idioma == 'en':
        return [w for w in re.findall(r'[a-z]+', SIN_MARCAS.sub(' ', texto).lower()) if w not in NUMEROS_EN]
    t = unicodedata.normalize('NFD', SIN_MARCAS.sub(' ', texto).lower())
    palabras = re.findall(r'\w+', ''.join(c for c in t if unicodedata.category(c) != 'Mn'))
    out: list[str] = []
    racha: list[str] = []

    def volcar() -> None:
        sueltas = all(len(w) == 1 for w in racha) and any(w not in 'aeiouy' for w in racha)
        if len(racha) >= 2 and (sueltas or LETRA_CLARA.intersection(racha)):
            out.append(''.join(LETRA.get(w, w) for w in racha))
        else:
            out.extend(racha)
        racha.clear()

    for w in palabras:
        if w.isdigit():
            volcar()
            out.extend(en_palabras(int(w)).split())
        elif w in LETRA or len(w) == 1:
            racha.append(w)
        else:
            volcar()
            out.append(w)
    volcar()
    return out


UNIDADES = [
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
DECENAS = {3: 'treinta', 4: 'cuarenta', 5: 'cincuenta', 6: 'sesenta', 7: 'setenta', 8: 'ochenta', 9: 'noventa'}


def en_palabras(n: int) -> str:
    """Número de 0 a 100 en palabras, sin tildes (whisper escribe "24" aunque se diga "veinticuatro").

    >>> en_palabras(7), en_palabras(24), en_palabras(32), en_palabras(40), en_palabras(2026)
    ('siete', 'veinticuatro', 'treinta y dos', 'cuarenta', '2026')
    """
    if n < 30:
        return UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        return DECENAS[d] + (f' y {UNIDADES[u]}' if u else '')
    return 'cien' if n == 100 else str(n)


def fonetica(palabra: str) -> str:
    """Clave de cómo suena una palabra en español latinoamericano (seseo, yeísmo, b = v, h muda).

    >>> [fonetica(w) for w in ('click', 'stock', 'whatsapp', 'zoom', 'clinicae', 'clinicay', 'corriges')]
    ['clic', 'estoc', 'guasap', 'sum', 'clinicai', 'clinicai', 'corrijes']
    >>> fonetica('cuenta') == fonetica('cuento')
    False
    """
    w = palabra
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


def comparar(esperado: list[str], oido: list[str]) -> list[tuple[str, str, str]]:
    """Diferencias (tipo, esperado, oído) entre dos listas de palabras.

    >>> comparar(normalizar('Cada segundo cuenta.'), normalizar('Cada segundo cuento.'))
    [('cambio', 'cuenta', 'cuento')]
    >>> comparar(['hola', 'mundo'], ['hola', 'mundo', 'braids'])
    [('sobra', '', 'braids')]
    >>> comparar(['hola', 'mundo'], ['mundo'])
    [('falta', 'hola', '')]

    Lo que suena igual no es un error: whisper escribe a su manera las palabras adaptadas.

    >>> comparar(['clic', 'en', 'estok', 'por', 'guasap', 'sin', 'zum'],
    ...          ['click', 'en', 'stock', 'por', 'whatsapp', 'sin', 'zoom'])
    []
    >>> comparar(['de', 'pendiente', 'en', 'clinikai'], ['dependiente', 'en', 'clinica', 'y'])
    []
    """
    tipos = {'replace': 'cambio', 'delete': 'falta', 'insert': 'sobra'}
    return [
        (tipos[op], ' '.join(esperado[a1:a2]), ' '.join(oido[b1:b2]))
        for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, esperado, oido, autojunk=False).get_opcodes()
        if op != 'equal' and fonetica(''.join(esperado[a1:a2])) != fonetica(''.join(oido[b1:b2]))
    ]
