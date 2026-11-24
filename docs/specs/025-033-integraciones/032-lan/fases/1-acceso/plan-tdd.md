# Spec 032, fase 1: Listener, dispositivos y emparejamiento

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../../../process/WARNING/README.md) (ficha `032-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-032/` o `tmp/spec-032/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

**Objetivo**: Un dispositivo se empareja y se autentica con su token. **AC**: AC-1, AC-2, AC-11, AC-4, AC-7, AC-3. **Depende de**: nada.

## Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor, servicio o comando → CLI y API → client). La numeración de ciclos es global a la spec; todo AC queda cubierto por al menos un ciclo y un fix empieza con un test de regresión en `server/tests/integration/test_bugs.py`.

#### Ciclo C1: Listener opt-in con TLS [AC-1, AC-2, AC-11]

- **RED**: `server/tests/integration/test_lan.py::test_ac1_apagado_solo_loopback`
  - Given los ajustes por defecto When arranca `serve` Then ningún socket fuera de loopback; activado sobre 127.0.0.2 (en el test), escucha con TLS.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `lan/cert.py`, `lan/server.py` y el arranque en `serve.py`. Verify: `uv run pytest server/tests/integration/test_lan.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo C2: Tokens por dispositivo [AC-4, AC-7]

- **RED**: `server/tests/unit/src/content_studio/lan/test_clients.py::test_ac4_sin_token_revocado_o_local_da_401`
  - WHEN se usa un token revocado THEN `authenticate` devuelve None; en la API, 401; los trabajos de otro dispositivo, 404.
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `lan/clients.py`, la columna `jobs.client_id` y el filtro. Verify: `uv run pytest server/tests -k lan -q`.
- **REFACTOR**: ninguno.

#### Ciclo C3: Emparejamiento [AC-3]

- **RED**: `server/tests/unit/src/content_studio/lan/test_pairing.py::test_ac3_pin_un_uso_vence_y_bloquea`
  - Given un reloj falso When se usa el PIN dos veces, tras 5 min o con 5 errores Then falla con `pairing_invalid` o `pairing_locked` (429).
  - Falla por el motivo esperado, no por setup.
- **GREEN**: `lan/pairing.py`, `POST /pair` (LAN) y `POST /lan/pairing` (local). Verify: `uv run pytest server/tests/unit/src/content_studio/lan -q`.
- **REFACTOR**: ninguno.

## Matriz e2e

No aplica: esta fase no crea ni cambia un flujo del client.
