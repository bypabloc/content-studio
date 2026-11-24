# Spec 033: verificación integral de las integraciones y cierre del lote

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `033-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-033/` o `tmp/spec-033/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | chore |
| Escala | Micro (1–2 archivos de código) |
| Rama | `chore/033-integral-verification` desde `origin/dev`, en `../content-studio-worktrees/033-integral-verification/` |
| Depende de | 025 a 032 fusionadas en `dev` |
| Origen | Pedido del usuario (2026-11-24) · [`docs/research/integraciones-locales/`](../../../research/integraciones-locales/README.md) |

## Objetivo

Comprobar juntas todas las puertas del lote (API compartida, MCP, carpetas de entrada, enlaces, «Enviar a» y red local) sobre la app instalada, dejar las fichas de `docs/process/` al día y borrar la carpeta del lote.

## 1. Precondición

```bash
git fetch origin dev
for b in chore/025-server-python chore/026-engines-python chore/027-client-deps feature/028-shared-server feature/029-mcp feature/030-hot-folders feature/031-windows-integration feature/032-lan; do
  git log origin/dev --merges --oneline | grep -q "$b" || echo "FALLA $b"
done
```

## 2. Contexto y decisiones

Cada spec del lote se verificó sola. Falta probar que conviven: un mismo server que despierta por el MCP, procesa una carpeta, recibe un enlace y atiende a un celular, sin dos workers ni dos modelos en la GPU.

- **D-1: un test de integración sin GPU recorre las puertas de Python en un solo server** — el CI no tiene GPU; un servicio falso basta para probar el ruteo. Se descarta repetir los tests de cada spec, porque no prueba la convivencia.
- **D-2: la prueba real es sobre la app instalada** (`app-check --binary`) — así se prueba lo que recibe el usuario (Python nueva, server compartido, accesos directos). Se descarta el checkout, porque no tiene instalador ni `SendTo`.

## 3. Fuera de alcance

- Arreglos de fondo: lo que falle va a un commit `fix:` pequeño o, si es grande, a `docs/process/02-next/`.
- Acceso desde internet.

## 4. Criterios de aceptación

- **AC-1**: Given un server compartido con un servicio falso When en el mismo proceso llegan un trabajo por `POST /jobs` con el token local, otro por MCP stdio, un archivo en una carpeta de entrada y otro desde un dispositivo de la LAN Then los cuatro terminan, hay un solo worker y `api.json` apunta a ese server.
- **AC-2**: WHEN se recorre 03 §2 sobre la app instalada THEN cada paso da lo esperado y las salidas reales pasan su «debe sonar».
- **AC-3**: WHEN se cierra el lote THEN no existe `docs/specs/025-033-integraciones/`, su fila ya no está en `docs/specs/README.md` y `docs/process/01-done/integrations.md` describe lo que hay.

## 5. Ciclo TDD

#### Ciclo C1: convivencia de las puertas [AC-1]

- **RED**: `server/tests/integration/test_integrations_together.py::test_ac1_cuatro_puertas_un_server`
  - Given una base temporal, un servicio falso registrado en `SERVICES` y la red local en 127.0.0.2 When llegan los cuatro pedidos Then terminan los cuatro, con un solo pid de server.
  - Falla por el motivo esperado, no por setup (antes del lote faltan las piezas; después, se escribe primero apagando la carpeta de entrada para verlo rojo).
- **GREEN**: solo el test; si falla por un bug, el fix va con su test en `server/tests/integration/test_bugs.py`.
- **REFACTOR**: ninguno.

## 6. Archivos

- Crear `server/tests/integration/test_integrations_together.py`. Verify: `uv run pytest server/tests/integration/test_integrations_together.py -q`.
- Modificar `docs/process/01-done/integrations.md` (Historial y `actualizada`), `docs/research/integraciones-locales/README.md` (una línea al inicio: implementado en las specs 025–032).
- Eliminar `docs/specs/025-033-integraciones/` (`git rm -r`) y su fila de `docs/specs/README.md`.

## 7. Verificación final

1. `uv run ruff check && uv run ruff format --check`, `python -m devtools test-runner --type=all`, `--type=e2e` y `--type=tauri-check`.
2. `python -m devtools bundle`, `tauri build` y `python -m devtools app-check run --binary=<instalador> --scenario=installed --scenario=031-sendto`.
3. Con la app instalada y cerrada: Claude Code con `studio mcp` pide una narración y una música de 30 s; el server arranca solo [AC-2].
4. Una carpeta de entrada `tmp/spec-033/entrada` con «Convertir a MP3» recibe un `.wav` copiado desde PowerShell [AC-2].
5. `Start-Process "content-studio://new/narration?text=Hola"` prellena sin encolar; «Enviar a» con dos archivos encola dos [AC-2].
6. Desde el celular u otra PC: emparejar, subir, convertir y descargar [AC-2].
7. Con `api.idle_minutes` = 1, sin carpetas `keep_awake` ni red local: el server se apaga y el siguiente pedido del MCP lo despierta [AC-2].
8. Duración, LUFS y espectrograma de cada salida en `tmp/spec-033/`, revisados por `image-reader`; las rutas de `out/` van en el PR para que el usuario escuche.

## 8. Commit y cierre

```text
chore: verificación integral de las integraciones locales y cierre del lote 025-033

- test de convivencia de api, mcp, carpetas de entrada y red local en un server
- fichas de 01-done al día y carpeta del lote borrada
```

- [ ] Fichas WARNING y PENDING del lote revisadas: las que ya se aplicaron se borran con su fila.
- [ ] `gh pr create --base dev` con las rutas de `out/` y el resultado de cada paso de §7; `gh pr checks <n> --watch`; `gh pr merge <n> --merge`.
- [ ] Desde el principal: `python -m devtools worktree close 033-integral-verification`.

## Matriz de verificación

| AC | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- |
| AC-1 | C1 | `server/tests/integration/test_integrations_together.py::test_ac1_cuatro_puertas_un_server` | solo pytest |
| AC-2 | — | `python -m devtools app-check run --binary=<instalador>` | §7, pasos 3 a 8 |
| AC-3 | — | `git ls-files docs/specs/025-033-integraciones` vacío | revisión del PR |

## WARNING y PENDING

- WARNING: ninguna propia; revisa las del lote.
- PENDING: lo que no se pudo probar de §7 (por ejemplo, sin celular), una ficha por paso.
