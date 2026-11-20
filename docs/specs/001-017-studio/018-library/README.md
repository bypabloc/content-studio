# 018: Biblioteca de medios

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `018-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. **La Biblioteca nunca borra nada sola**: todo borrado lo pide el usuario, con confirmación, y va a la papelera de Windows. Las carpetas vigiladas solo se leen, salvo que el usuario renombre, mueva o borre un archivo. Las pruebas usan `tmp/spec-018/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 20 archivos entre server y client) |
| Rama | `feature/018-library` desde `origin/dev`, en `../content-studio-worktrees/018-library/` |
| Depende de | [017](../017-editor-effects/README.md) (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Un solo lugar para todo lo generado por el estudio y lo que haya en las carpetas que el usuario agregue. Tiene búsqueda (también en el texto del guion o de la transcripción), filtros, etiquetas, proyectos, vista de grilla o lista y reproductor. Desde ahí se puede ver el origen de cada archivo y repetirlo, mandarlo a otra sección, renombrarlo, moverlo o mandarlo a la papelera, y hay un resumen del espacio con vistas para liberarlo.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Índice: ítems desde trabajos y carpetas vigiladas, metadatos y miniaturas en caché de disco | PEN |
| 2 | Búsqueda, filtros, etiquetas y proyectos | PEN |
| 3 | Acciones: origen y repetir, mandar a…, renombrar, mover y papelera | PEN |
| 4 | Espacio: resumen, lo más pesado y tomas no elegidas | PEN |
| 5 | Client: Biblioteca en grilla y lista con detalle | PEN |

## Decisiones clave

* D-1: las tablas `library_*` guardan solo rutas, metadatos numéricos, etiquetas y relaciones (migración 6, sin BLOB). Las miniaturas van en una caché de disco.
* D-2: las carpetas vigiladas se escanean al abrir la Biblioteca y con «Actualizar», sin un watcher en vivo.
* D-3: la búsqueda en el texto lee los JSON de guion y transcripción que ya están en disco. La base no guarda ese texto.
* D-4: la papelera es la de Windows, con `send2trash`.

## WARNING y PENDING

* WARNING: `018-send2trash.md` (dependencia nueva) y `018-busqueda-en-disco.md` (límite de escala).
* PENDING: ninguna.
