# Spec <NN>: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../process/WARNING/README.md) (ficha `<NN>-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-<NN>/` o `tmp/spec-<NN>/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

<Si depende de otra spec: comandos contra `origin/dev` que lo comprueban y se corren antes del primer commit (plan-format.md §5). Si no, «no aplica».>

```bash
git log origin/dev --merges --oneline | grep -q '<rama de la dependencia>' || echo FALLA
git cat-file -e origin/dev:<ruta que usa esta spec> || echo FALLA
```

## 2. Contexto

<Cómo funciona hoy y qué problema causa, escrito para alguien que no estuvo en la conversación.>

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| <término> | <qué es> | `<símbolo>` / `<clave>` |

### Hallazgos de la exploración

Cada hallazgo con su evidencia: archivo y símbolo (de `graphify query|explain`) o medición actual con fecha (tiempos, VRAM, LUFS).

- **<Hallazgo>.** <Evidencia: `server/src/content_studio/<…>.py` (`<función>`) o «medido el <fecha>: <valor>»>.

## 3. Solución

<Resumen en 2-4 puntos de qué se construye y dónde.>

Cada decisión pasa por la escalera de plan-format.md §0 (¿debe existir? ¿ya existe? ¿stdlib o una dependencia que ya está?).

- **D-1: <qué>** — <por qué>. Se descarta <alternativa> porque <razón>.

## 4. Fuera de alcance

- <Lo que esta spec no hace; si queda pendiente, su ficha en `docs/process/02-next/` o `PENDING/`>.

## 5. Criterios de aceptación

BDD (`Given/When/Then`) o EARS (`WHEN/THEN`); cada uno verificable con una prueba (pytest, doctest o una medición de la salida real).

- **AC-1**: WHEN <acción> THEN <resultado observable>.
- **AC-2**: Given <estado> When <acción> Then <resultado>.

## 6. Debe sonar / no debe sonar

<Solo si toca la salida de audio. Si no, «no aplica».>

| Salida | Debe | No debe |
| :--- | :--- | :--- |
| <comando y archivo> | <duración, LUFS, carácter> | <voz en la música, cortes, clipping, silencios> |
