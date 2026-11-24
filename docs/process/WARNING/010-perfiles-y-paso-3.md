# 010: perfiles de voz y paso 3 de move-data (ciclo 1)

- **Contexto**: D-1 pide perfiles en `reference/<perfil>/`, `--profile` en lugar de `--ref` y el paso 3 de `move-data` que lleva las referencias actuales al perfil `default` («Mi voz»). La spec no fija cómo se integra con el paso 2 ni qué pasa con los trabajos viejos.
- **Elegida**:
  - El paso 3 usa el mismo mapa de renombres que el paso 2: `devtools/migrations.py::profile_path()` se aplica dentro de `plan_names`. Así comparten la detección de choques, la idempotencia y el «nunca sobrescribe». `ensure_default_profile()` crea `profile.json` («Mi voz») cuando la carpeta existe y no lo tiene.
  - Los `.txt` versionados de `reference/` se mueven con `git mv` en el commit de T1. Git los tiene versionados, así que `move-data` no los toca; los `.wav`, que no están en git, sí los mueve.
  - `profiles.reference_for(profile, style, suffix)` es el único armador de rutas de perfil. `profiles.folder()` rechaza un nombre que no sea slug, así que `../x` no sale de `reference/`.
  - `narration/voices/build.py` lee la transcripción de cada estilo del perfil `default`, como antes la leía de la raíz.
  - `--profile` entra en el `FLAGS` del servicio y en `NARRATION_FLAGS` del CLI. Un trabajo viejo con `ref` en sus params pierde esa clave y, si se reintenta, usa el perfil `default`.
  - AC-2 se verifica a nivel módulo (`test_profiles.py`) en este ciclo. Su parte de API (201, 200, 204 y 409) llega con las rutas del ciclo 2.
  - `styles_status()` (D-1) llega con las tomas del ciclo 2: sin tomas no hay estado del chequeo que mostrar.
- **Descartadas**:
  - Un paso 4 aparte para el perfil: el mismo mapa de renombres basta y evita recorrer los datos dos veces.
  - Cambiar `devtools/worktree.py`: ya busca los audios con `rglob`, así que `reference/default/*.wav` se copia sin cambios.
- **Cómo revertir**: revertir el commit `feat: perfiles de voz propios...` devuelve `--ref` y los `.txt` a la raíz de `reference/`. `move-data` no se vuelve a correr sobre los datos hasta la T9.
