"""Descarga de la base cruda de cada voz del catálogo, con caché en narration/voces/.fuentes. Solo stdlib + ffmpeg."""

from __future__ import annotations

import io
import re
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from content_studio.rutas import VOCES

UA = {'User-Agent': 'content-studio-voces'}
PAUSA_PARTES = 0.4  # s entre las partes de una base armada con varios clips


class ZipRemoto(io.RawIOBase):
    """Archivo HTTP de solo lectura con `Range`: zipfile lee el índice y los miembros pedidos, no el zip entero
    (los de OpenSLR pesan ~0.8 GB y cada clip ~1 MB)."""

    def __init__(self, url: str):
        self.url, self.pos = url, 0
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers=UA)) as r:
            self.size = int(r.headers['Content-Length'])

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, off: int, whence: int = 0) -> int:
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def readinto(self, b: bytearray) -> int:
        if self.pos >= self.size:
            return 0
        fin = min(self.pos + len(b), self.size) - 1
        rango = {**UA, 'Range': f'bytes={self.pos}-{fin}'}
        with urllib.request.urlopen(urllib.request.Request(self.url, headers=rango)) as r:
            data = r.read()
        b[: len(data)] = data
        self.pos += len(data)
        return len(data)


def bajar(url: str, miembro: str | None = None) -> Path:
    """Archivo de la fuente en la caché narration/voces/.fuentes: la URL entera o, con `miembro`, ese archivo de
    un zip."""
    cache = VOCES / '.fuentes' / (miembro or url.rsplit('/', 1)[-1].replace('%28', '(').replace('%29', ')'))
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        print(f'Descargando {url}' + (f' → {miembro}' if miembro else ''))
        if miembro:
            with zipfile.ZipFile(io.BufferedReader(ZipRemoto(url), 1 << 16)) as z:
                nombre = next(n for n in z.namelist() if n.endswith('/' + miembro) or n == miembro)
                cache.write_bytes(z.read(nombre))
        else:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r, open(cache, 'wb') as f:
                shutil.copyfileobj(r, f)
    return cache


def tramo_voz(clip: Path) -> tuple[float, float | None]:
    """(inicio, fin) de la voz en un clip corto: del fin del silencio inicial al primer silencio de 0.8 s o más.
    silenceremove no sirve en los clips de OpenSLR: un clic o una respiración al final frena el recorte."""
    err = subprocess.run(
        ['ffmpeg', '-hide_banner', '-i', str(clip), '-af', 'silencedetect=n=-40dB:d=0.3', '-f', 'null', '-'],
        capture_output=True,
        text=True,
    ).stderr
    return tramo_de_silencios(
        [float(x) for x in re.findall(r'silence_start: ([\d.]+)', err)],
        [float(x) for x in re.findall(r'silence_end: ([\d.]+)', err)],
    )


def tramo_de_silencios(ini: list[float], fin: list[float]) -> tuple[float, float | None]:
    """Con los silencios de silencedetect, el tramo con voz (0.08 s antes y 0.12 s después de margen).

    >>> tramo_de_silencios([0.0, 4.1], [1.5, 6.0])     # silencio inicial de 1.5 s, voz hasta 4.1 s
    (1.42, 4.22)
    >>> tramo_de_silencios([0.0, 2.0, 3.0], [1.0, 2.4]) # la pausa de 0.4 s no corta; la que empieza en 3.0 sí
    (0.92, 3.12)
    >>> tramo_de_silencios([], [])                      # sin silencios: el clip entero
    (0.0, None)
    """
    a = fin[0] if ini and ini[0] < 0.05 else 0.0
    b = next((s for s, e in zip(ini, fin + [1e9], strict=False) if s > a and e - s >= 0.8), None)
    return round(max(a - 0.08, 0.0), 3), round(b + 0.12, 3) if b else None


def descargar(ficha: dict, destino: Path) -> None:
    """La base cruda de la voz, sin procesar: el tramo `inicio_s`/`dur_s` de `url`, o las `partes` (clips cortos del
    mismo hablante, p. ej. de OpenSLR) sin el silencio de los bordes y unidas con PAUSA_PARTES s entre ellas."""
    mono = ['-ac', '1', '-c:a', 'pcm_s24le']
    if 'partes' not in ficha:
        corte = ['-ss', str(ficha['inicio_s']), '-t', str(ficha['dur_s'])] if 'inicio_s' in ficha else []
        subprocess.run(
            ['ffmpeg', '-v', 'error', '-y', *corte, '-i', str(bajar(ficha['url'])), *mono, str(destino)], check=True
        )
        return
    clips = [bajar(p['url'], p.get('miembro')) for p in ficha['partes']]
    filtros = []
    for i, c in enumerate(clips):
        a, b = tramo_voz(c)
        filtros.append(
            f'[{i}]aformat=channel_layouts=mono,atrim=start={a:.3f}'
            + (f':end={b:.3f}' if b else '')
            + ',asetpts=N/SR/TB'
            + (f',apad=pad_dur={PAUSA_PARTES}' if i < len(clips) - 1 else '')
            + f'[c{i}]'
        )
    union = ''.join(f'[c{i}]' for i in range(len(clips))) + f'concat=n={len(clips)}:v=0:a=1'
    entradas = [a for c in clips for a in ('-i', str(c))]
    subprocess.run(
        [
            'ffmpeg',
            '-v',
            'error',
            '-y',
            *entradas,
            '-filter_complex',
            ';'.join(filtros) + ';' + union,
            *mono,
            str(destino),
        ],
        check=True,
    )
