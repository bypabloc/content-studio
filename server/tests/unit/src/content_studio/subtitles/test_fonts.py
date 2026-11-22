"""Fuentes de Subtítulos (spec 014, D-6; AC-8): las incluidas en `server/data/fonts` y las del sistema.

Las del sistema se simulan con una copia de una fuente incluida; la familia y el estilo salen de la tabla `name`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from content_studio import paths
from content_studio.subtitles import fonts

BUNDLED = paths.DATA / 'fonts'
MONTSERRAT = BUNDLED / 'montserrat' / 'Montserrat-Regular.ttf'
FAMILIES = {'Montserrat', 'Inter', 'Inter Tight', 'Poppins', 'Bebas Neue'}


def test_reads_the_family_and_the_style_of_a_bundled_font():
    """La familia y el estilo salen de la tabla `name`, con respaldo a los nombres legados."""
    assert fonts.read_names(MONTSERRAT) == ('Montserrat', 'Regular')
    assert fonts.read_names(BUNDLED / 'montserrat' / 'Montserrat-ExtraBold.ttf') == ('Montserrat', 'ExtraBold')


def test_a_file_that_is_not_a_font_is_skipped(tmp_path):
    """Un archivo con extensión de fuente que no lo es no rompe la lista: se ignora."""
    broken = tmp_path / 'nota.ttf'
    broken.write_bytes(b'no es una fuente')

    assert fonts.read_names(broken) is None


def test_lists_the_five_bundled_families_with_their_styles():
    """AC-8: las 5 familias incluidas con `bundled: true`, con sus estilos."""
    listed = {entry['family']: entry for entry in fonts.list_fonts(BUNDLED, [])}

    assert set(listed) == FAMILIES
    assert all(entry['bundled'] for entry in listed.values())
    assert listed['Montserrat']['styles'] == ['Bold', 'ExtraBold', 'Regular']
    assert listed['Montserrat']['path'].endswith('Montserrat-Regular.ttf')


def test_system_fonts_come_from_the_given_files_and_are_not_bundled(tmp_path):
    """La carpeta del sistema se simula con una copia de una fuente: aparece con `bundled: false`."""
    system_file = tmp_path / 'segoeui.ttf'
    shutil.copy(MONTSERRAT, system_file)

    system = [entry for entry in fonts.list_fonts(BUNDLED, [system_file]) if not entry['bundled']]

    assert [(entry['family'], entry['bundled']) for entry in system] == [('Montserrat', False)]


def test_a_broken_system_file_is_skipped(tmp_path):
    """Un archivo del sistema que no se puede leer no cambia la lista de las incluidas."""
    broken = tmp_path / 'roto.otf'
    broken.write_bytes(b'x')

    assert fonts.list_fonts(BUNDLED, [broken]) == fonts.list_fonts(BUNDLED, [])


def test_windows_font_folders_come_from_the_environment(tmp_path):
    """En Windows, las carpetas de fuentes salen de WINDIR y de LOCALAPPDATA (simulados)."""
    env = {'WINDIR': str(tmp_path / 'Win'), 'LOCALAPPDATA': str(tmp_path / 'Local')}

    assert fonts.system_font_dirs(env) == [
        tmp_path / 'Win' / 'Fonts',
        tmp_path / 'Local' / 'Microsoft' / 'Windows' / 'Fonts',
    ]


def test_files_serves_the_bundled_and_the_windows_font_folders(tmp_path):
    """/files sirve la carpeta de fuentes incluida y, en Windows, las del sistema (spec 014, D-6)."""
    env = {'WINDIR': str(tmp_path / 'Win'), 'LOCALAPPDATA': str(tmp_path / 'Local')}

    roots = fonts.font_roots(BUNDLED, platform='win32', env=env)

    assert roots == [
        BUNDLED.resolve(),
        (tmp_path / 'Win' / 'Fonts').resolve(),
        (tmp_path / 'Local' / 'Microsoft' / 'Windows' / 'Fonts').resolve(),
    ]


def test_posix_takes_the_font_files_from_fc_list(monkeypatch):
    """En POSIX, las fuentes del sistema vienen de `fc-list` (simulado)."""

    class Done:
        stdout = '/usr/share/fonts/a.ttf\n/usr/share/fonts/b.otf\n'

    monkeypatch.setattr(fonts.shutil, 'which', lambda name: '/usr/bin/fc-list')
    monkeypatch.setattr(fonts.subprocess, 'run', lambda *args, **kwargs: Done())

    assert fonts.system_font_files({}, platform='linux') == [
        Path('/usr/share/fonts/a.ttf'),
        Path('/usr/share/fonts/b.otf'),
    ]
