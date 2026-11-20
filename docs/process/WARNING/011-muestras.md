# 011: muestras de 10 s por preset como trabajo reanudable (AC-5)

- **Contexto**: el buscador de Música tiene un ▶ por preset que suena una muestra de 10 s. Hace falta una muestra por preset, generada una vez y reutilizada; regenerarla no debe cambiar el clip.
- **Elegida**:
  - `services/music_samples.py` es el servicio `music.samples` (`RESOURCE = 'gpu'`: el worker toma el candado; una muestra detrás de otra). `music/samples_main.py` corre en el venv de ACE-Step, sin planificador LM (`no_lm`), 10 s y **semilla fija 1234** para todas.
  - La semilla llega al motor por `a.seed`. Si está, `acestep.py` usa `seeds=[seed]`; si no, sigue con una semilla nueva por pista, como antes.
  - Las muestras van a `server/data/music/samples/<preset>.wav`, no a `out/`. Cada trabajo deja `out/music/<fecha>-<id>-music-samples/params.json`, sin audio.
  - Solo se generan las que faltan; `force` las regenera. Si el motor falla, la muestra vieja se borra antes: no queda como si fuera nueva.
  - `/files` sirve `samples/`. Las carpetas permitidas están en `api/app.py` (no en `api/routes/files.py`, como dice el plan: ahí no hay lista de carpetas).
  - `worktree prepare` crea `server/data/music/samples/` en el principal y la enlaza al worktree. Se crea antes de calcular lo que falta, para que el enlace exista aunque esté vacía. `.gitignore` excluye los WAV.
  - `studio music samples [--styles …] [--force]`. `--model` deja de ser obligatorio en el parser de `studio music` (`music_flags(model_required=False)`) y `submit.music_params` lo exige como error de uso (código 2, mismo mensaje que argparse). Así `music samples` no lo pide y `studio music` sin `--model` sigue fallando igual.
- **Descartadas**:
  - Semilla aleatoria: cada regeneración cambiaría el clip del buscador.
  - Muestras en `out/music/`: `out/` es de cada trabajo; el buscador necesita una ruta fija por preset.
  - Enlazar `samples/` solo si ya existe en el principal: en un principal sin muestras el enlace nunca se crearía.
- **Cómo revertir**: quitar `music.samples` de `SERVICES`, `services/music_samples.py`, `music/samples_main.py`, el subcomando en `cli/main.py`, `samples_params` y `SAMPLES_FLAGS` en `cli/submit.py`, la ruta en `api/app.py`, la línea de `devtools/worktree.py` y de `.gitignore`, y el parámetro `seed` de `acestep.py`.
- **Cómo comprobarla**: `services/test_music_samples.py` (saltea las existentes, `force`, progreso por preset), `music/test_samples_main.py`, `cli/test_main.py` (enrutado y `--model`), `cli/test_submit.py` y `devtools/tests/unit/test_worktree.py`. La corrida real: `uv run studio --db <tmp> music samples --styles lofi-chill` deja `server/data/music/samples/lofi-chill.wav` de 10 s (`ffprobe`).
- **Pendiente**: generar las 126 muestras con el comando anterior, una corrida larga en GPU. Ficha en [`../PENDING/011-generar-muestras.md`](../PENDING/011-generar-muestras.md).
