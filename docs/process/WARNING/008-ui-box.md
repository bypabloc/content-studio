# 008: `UIBox` es el contenedor genérico, y solo lo importan las moléculas y los organismos

- **Contexto**: las moléculas y los organismos de klinikae tienen `div` y `span` internos. Un átomo que envuelve esas etiquetas hace falta para que una molécula o un organismo no escriba una etiqueta nativa (D-4; la etapa `ui-structure` que la hace cumplir es de D-5).
- **Elegida**: `UIBox` con `as` (`div`, `span`, `section`, `header`, `nav`, `aside`, `main` o `footer`), `className` y el resto de atributos del `div`. `features/` y `app/` no lo importan: su layout sale de `UIStack` (ahora con `direction`, `align` y `justify`), `UIGrid`, `UICard`, `UIPage` y `UIText`.
- **Descartadas**:
  - Dejar que cada molécula use `div` y que la etapa lo tolere: rompe la regla de D-4.
  - Un `UIBox` que acepte cualquier etiqueta: la lista cerrada es lo que hace que la etapa `ui-structure` sea sencilla de explicar.
- **Cómo revertir**: sustituir los `UIBox` de moléculas y organismos por `div` y quitar la etapa `ui-structure` (D-5).
- **Cómo comprobarla**: `bun run --cwd client test -- components/atoms/UIBox` (cuatro casos: etiqueta por defecto, `as`, `className`, atributos).
- **Antes de**: el merge a `dev`.
