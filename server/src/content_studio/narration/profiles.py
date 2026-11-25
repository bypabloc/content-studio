"""Perfiles de voz propia (spec 010, D-1): cada perfil es una carpeta de reference/ con su referencia por estilo.

`reference/<perfil>/profile.json` guarda el nombre visible; `<estilo>.wav` y `<estilo>.txt` son la referencia elegida, y
`takes/<estilo>/` sus tomas. Borrar nunca borra bytes: un perfil con archivos va a `reference/.trash/`.

>>> slugify('Mi voz nueva'), reference_for('default', 'expert').name
('mi-voz-nueva', 'expert.wav')
"""

from __future__ import annotations

import json
import re
import shutil
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

from content_studio import paths
from content_studio.narration import recording_kit

DEFAULT = 'default'  # las referencias de antes de la 010; move-data (paso 3) les pone el nombre «Mi voz»
PROFILE_FILE = 'profile.json'
TRASH = '.trash'
SLUG = re.compile(r'[a-z0-9][a-z0-9-]*')


class ProfileExists(Exception):
    """Ya hay un perfil con esa carpeta: crear nunca pisa uno existente."""


class ProfileNotEmpty(Exception):
    """El perfil tiene archivos: para borrarlo hace falta `confirm`, y entonces va a la papelera."""


def _slug_ok(profile: object) -> bool:
    """True si el nombre es una carpeta válida: sin separadores ni `..`, así no sale de reference/."""
    return isinstance(profile, str) and SLUG.fullmatch(profile) is not None


def folder(profile: str) -> Path:
    """Carpeta del perfil dentro de reference/; un nombre que no es slug se rechaza."""
    if not _slug_ok(profile):
        raise ValueError(f'not a profile name: {profile!r}')
    return paths.references_dir() / profile


def exists(profile: str) -> bool:
    """True si el perfil existe; un nombre que no es slug no existe."""
    return _slug_ok(profile) and folder(profile).is_dir()


def reference_for(profile: str, style: str, suffix: str = '.wav') -> Path:
    """Ruta de la referencia de un estilo en un perfil: el audio (`.wav`) o su transcripción (`.txt`)."""
    return folder(profile) / f'{style}{suffix}'


def slugify(name: str) -> str:
    """Nombre visible a carpeta: sin acentos, en minúsculas y con guiones («Spec 010» → «spec-010»)."""
    plain = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '-', plain.lower()).strip('-')


def _read(profile: str) -> dict:
    """El profile.json del perfil; vacío si no existe."""
    target = folder(profile) / PROFILE_FILE
    return json.loads(target.read_text(encoding='utf-8')) if target.is_file() else {}


def _write(profile: str, data: dict) -> None:
    """Guarda el profile.json del perfil, que debe existir."""
    (folder(profile) / PROFILE_FILE).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def create(name: str) -> str:
    """Crea un perfil con ese nombre visible y devuelve su carpeta (el slug del nombre)."""
    slug = slugify(name)
    if not _slug_ok(slug):
        raise ValueError(f'the profile needs a name with letters or digits: {name!r}')
    if exists(slug):
        raise ProfileExists(slug)
    folder(slug).mkdir(parents=True)
    _write(slug, {'name': name, 'created_at': datetime.now(UTC).isoformat(timespec='seconds')})
    return slug


def record_consent(profile: str, text: str) -> None:
    """Guarda el permiso del dueño la primera vez que se importa algo al perfil; las siguientes no lo cambian."""
    data = _read(profile)
    if 'consent' not in data:
        stamp = datetime.now(UTC).isoformat(timespec='seconds')
        _write(profile, {**data, 'consent': {'accepted_at': stamp, 'text': text}})


def rename(profile: str, name: str) -> None:
    """Cambia el nombre visible; la carpeta y las referencias no cambian."""
    _write(profile, {**_read(profile), 'name': name})


def name_of(profile: str) -> str:
    """El nombre visible del perfil; sin profile.json, su carpeta."""
    return _read(profile).get('name', profile)


def styles(profile: str) -> list[str]:
    """Estilos con referencia (`.wav`) en el perfil, en orden alfabético."""
    return sorted(p.stem for p in folder(profile).glob('*.wav'))


def takes_dir(profile: str, style: str) -> Path:
    """Carpeta de las tomas de un estilo en el perfil."""
    return folder(profile) / 'takes' / style


def take_numbers(profile: str, style: str) -> list[int]:
    """Números de las tomas del estilo, en orden."""
    return sorted(int(p.stem) for p in takes_dir(profile, style).glob('*.wav') if p.stem.isdigit())


def styles_status(profile: str) -> list[dict]:
    """Cada estilo del kit: si tiene referencia elegida y cuántas tomas tiene."""
    return [
        {
            'style': style,
            'chosen': reference_for(profile, style).is_file(),
            'takes': len(take_numbers(profile, style)),
            'reference': paths.playable(reference_for(profile, style)),
        }
        for style in recording_kit.STYLES
    ]


def delete(profile: str, confirm: bool = False) -> None:
    """Borra un perfil vacío. Con archivos hace falta `confirm`, y entonces el perfil entero va a reference/.trash/."""
    where = folder(profile)
    if all(p.name == PROFILE_FILE for p in where.iterdir()):
        shutil.rmtree(where)
        return
    if not confirm:
        raise ProfileNotEmpty(profile)
    target = paths.references_dir() / TRASH / datetime.now().strftime('%Y-%m-%d-%H%M%S-%f') / profile
    target.parent.mkdir(parents=True)
    shutil.move(str(where), str(target))


def list_profiles() -> list[dict]:
    """Los perfiles con su nombre visible y los estilos que ya tienen: un perfil parcial solo ofrece esos."""
    if not paths.references_dir().is_dir():
        return []
    return [
        {'id': d.name, 'name': name_of(d.name), 'styles': styles(d.name)}
        for d in sorted(paths.references_dir().iterdir())
        if d.is_dir() and _slug_ok(d.name)
    ]
