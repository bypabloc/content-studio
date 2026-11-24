"""Descarga de la base cruda de cada voz del catálogo, con caché en
server/data/narration/voices/.fuentes. Solo stdlib + ffmpeg."""

from __future__ import annotations

import io
import re
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from content_studio.paths import voices_dir

UA = {'User-Agent': 'content-studio-voces'}
PAUSE_PARTS = 0.4  # s entre las partes de una base armada con varios clips


class RemoteZip(io.RawIOBase):
    """Archivo HTTP de solo lectura con `Range`: zipfile lee el índice y los miembros pedidos, no el zip entero
    (los de OpenSLR pesan ~0.8 GB y cada clip ~1 MB)."""

    def __init__(self, url: str):
        """Lee un archivo remoto por rangos HTTP, sin bajarlo entero."""
        self.url, self.pos = url, 0
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers=UA)) as r:
            self.size = int(r.headers['Content-Length'])

    def readable(self) -> bool:
        """Siempre legible."""
        return True

    def seekable(self) -> bool:
        """Siempre buscable."""
        return True

    def tell(self) -> int:
        """Posición actual."""
        return self.pos

    def seek(self, off: int, whence: int = 0) -> int:
        """Mueve la posición como `io` (SEEK_SET, SEEK_CUR, SEEK_END)."""
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def readinto(self, b: bytearray) -> int:
        """Lee en `b` desde la posición actual con un rango HTTP."""
        if self.pos >= self.size:
            return 0
        end = min(self.pos + len(b), self.size) - 1
        headers = {**UA, 'Range': f'bytes={self.pos}-{end}'}
        with urllib.request.urlopen(urllib.request.Request(self.url, headers=headers)) as r:
            data = r.read()
        b[: len(data)] = data
        self.pos += len(data)
        return len(data)


def fetch(url: str, member: str | None = None) -> Path:
    """Archivo de la fuente en la caché server/data/narration/voices/.fuentes:
    la URL entera o, con `miembro`, ese archivo de
    un zip."""
    cache = voices_dir() / '.fuentes' / (member or url.rsplit('/', 1)[-1].replace('%28', '(').replace('%29', ')'))
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        print(f'Downloading {url}' + (f' → {member}' if member else ''))
        if member:
            with zipfile.ZipFile(io.BufferedReader(RemoteZip(url), 1 << 16)) as z:
                name = next(n for n in z.namelist() if n.endswith('/' + member) or n == member)
                cache.write_bytes(z.read(name))
        else:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r, open(cache, 'wb') as f:
                shutil.copyfileobj(r, f)
    return cache


def span_voice(clip: Path) -> tuple[float, float | None]:
    """(inicio, fin) de la voz en un clip corto: del fin del silencio inicial al primer silencio de 0.8 s o más.
    silenceremove no sirve en los clips de OpenSLR: un clic o una respiración al final frena el recorte."""
    err = subprocess.run(
        ['ffmpeg', '-hide_banner', '-i', str(clip), '-af', 'silencedetect=n=-40dB:d=0.3', '-f', 'null', '-'],
        capture_output=True,
        text=True,
    ).stderr
    return span_de_silences(
        [float(x) for x in re.findall(r'silence_start: ([\d.]+)', err)],
        [float(x) for x in re.findall(r'silence_end: ([\d.]+)', err)],
    )


def span_de_silences(ini: list[float], end: list[float]) -> tuple[float, float | None]:
    """Con los silencios de silencedetect, el tramo con voz (0.08 s antes y 0.12 s después de margen).

    >>> span_de_silences([0.0, 4.1], [1.5, 6.0])     # silence inicial de 1.5 s, voice until 4.1 s
    (1.42, 4.22)
    >>> span_de_silences([0.0, 2.0, 3.0], [1.0, 2.4]) # la pause de 0.4 s no corta; la que empieza en 3.0 sí
    (0.92, 3.12)
    >>> span_de_silences([], [])                      # no silences: el clip entero
    (0.0, None)
    """
    a = end[0] if ini and ini[0] < 0.05 else 0.0
    b = next((s for s, e in zip(ini, end + [1e9], strict=False) if s > a and e - s >= 0.8), None)
    return round(max(a - 0.08, 0.0), 3), round(b + 0.12, 3) if b else None


def download(sheet: dict, destination: Path) -> None:
    """La base cruda de la voz, sin procesar: el tramo `inicio_s`/`dur_s` de `url`, o las `partes` (clips cortos del
    mismo hablante, p. ej. de OpenSLR) sin el silencio de los bordes y unidas con PAUSA_PARTES s entre ellas."""
    mono = ['-ac', '1', '-c:a', 'pcm_s24le']
    if 'parts' not in sheet:
        cut = ['-ss', str(sheet['start_s']), '-t', str(sheet['dur_s'])] if 'start_s' in sheet else []
        subprocess.run(
            ['ffmpeg', '-v', 'error', '-y', *cut, '-i', str(fetch(sheet['url'])), *mono, str(destination)], check=True
        )
        return
    clips = [fetch(p['url'], p.get('member')) for p in sheet['parts']]
    filters = []
    for i, c in enumerate(clips):
        a, b = span_voice(c)
        filters.append(
            f'[{i}]aformat=channel_layouts=mono,atrim=start={a:.3f}'
            + (f':end={b:.3f}' if b else '')
            + ',asetpts=N/SR/TB'
            + (f',apad=pad_dur={PAUSE_PARTS}' if i < len(clips) - 1 else '')
            + f'[c{i}]'
        )
    union = ''.join(f'[c{i}]' for i in range(len(clips))) + f'concat=n={len(clips)}:v=0:a=1'
    entries = [a for c in clips for a in ('-i', str(c))]
    subprocess.run(
        [
            'ffmpeg',
            '-v',
            'error',
            '-y',
            *entries,
            '-filter_complex',
            ';'.join(filters) + ';' + union,
            *mono,
            str(destination),
        ],
        check=True,
    )
