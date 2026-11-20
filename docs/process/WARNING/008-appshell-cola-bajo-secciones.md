# 008: la cola va bajo las secciones de la barra, no a la derecha

- **Contexto**: AC-7 dice «la cola a la derecha», y D-7 llama `aside` al panel de la cola. La Ronda 5 de la entrevista eligió «sidebar con secciones agrupadas + panel de cola abajo», y la app ya la muestra bajo las secciones. El mismo AC-7 pide que «Ajustes, la cola y Narración se ven y funcionan como antes».
- **Elegida**: el panel de la cola va bajo las secciones, dentro de la barra (slot `aside` de `UIAppShell`), y se oculta al colapsar. El pie (tema y versión) queda al final de la barra. El botón que colapsa va en la cabecera de la barra, junto al nombre, y no hay barra superior: la app no la tenía y el aspecto sigue como antes.
- **Descartadas**: una columna derecha (contradice la Ronda 5 y el «como antes»); una barra superior con el botón (agrega una franja de 64 px que la app no tenía).
- **Cómo revertir**: mover `aside` a una columna propia en `UIAppShell` y en `app/Shell.tsx`, en un solo commit.
- **Cómo comprobarla**: `client/tests/unit/src/app/Shell.test.tsx` (la barra con el tema y la versión, y la preferencia guardada) y `tests/e2e/shell/happy-sidebar-collapse.e2e.ts`.
- **Pendiente**: la mirada en la app real del panel de la cola y de la cabecera, en [PENDING/008-revision-visual-organismos](../PENDING/008-revision-visual-organismos.md).
