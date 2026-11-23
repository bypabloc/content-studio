# 018: Editor (visual): pistas de video e imagen con transparencia, transformar con keyframes, transiciones y exportar video

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `018-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. El editor nunca modifica sus archivos de entrada; los proxies van a la caché del proyecto. Las pruebas usan medios generados en `tmp/spec-018/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 25 archivos entre server y client) |
| Rama | `feature/018-editor-visual` desde `origin/dev`, en `../content-studio-worktrees/018-editor-visual/` |
| Depende de | [017](../017-editor-core/README.md) (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (2026-11-19), lote [001-017-studio](../README.md). Segunda de tres del Editor |

## Objetivo

Que el Editor de la 017 sea un NLE de video: pistas ilimitadas de video e imagen (PNG y WebP con transparencia, como un logo, y video WebM con alfa) apiladas sobre un lienzo, con posición, escala, rotación, opacidad y recorte animables con keyframes, transiciones entre clips, una vista previa en tiempo real y la exportación a MP4 o WebM con la mezcla de audio de la 017.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Esquema v2 (lienzo, pistas visuales, transformación y keyframes) e interpolación compartida | IMP (`584b402`) |
| 2 | Proxies y fotograma exacto bajo demanda | IMP (`87edebf`) |
| 3 | Render de video: capas, keyframes y transiciones en `filter_complex` | IMP (`5d9394a`, `0a35e9b`) |
| 4 | Client: compositor WebGL2 de vista previa | PEN |
| 5 | Client: lienzo, inspector, keyframes y transiciones en la línea de tiempo | PEN |

## Decisiones clave

* D-1: `project.json` v2 con `canvas`, pistas `video` (video, imagen o, en la 019, texto) y `transform` con keyframes; `migrate` sube la v1 sin pérdida.
* D-2: la interpolación (lineal, suave y mantener) se define una vez y se espeja con fixtures, como en la 017.
* D-3: exportar arma capas con `overlay` y expresiones por tramos de `t` para los keyframes, y `xfade` para las transiciones; nada de `sendcmd` ni `zmq`.
* D-4: vista previa con un compositor WebGL2 propio sobre proxies H.264 (o VP9 con alfa); un fotograma exacto del server para comparar y para el test de paridad.

## WARNING y PENDING

* WARNING: `018-paridad-preview-export.md` (umbral de SSIM y casos), `018-proxies.md` (resolución, códec y caché), `018-render-video.md` (crop animado y tamaño de transformaciones) y `018-transiciones.md` (lista elegida).
* PENDING: ninguna.
