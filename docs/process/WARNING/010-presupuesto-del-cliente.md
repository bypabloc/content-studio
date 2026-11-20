# 010: el presupuesto del JS inicial sube de 228 a 232 kB por la pantalla de Mis voces

- **Contexto**: la etapa `budget` mide todo el JS del build, en gzip, contra `client/budget.json` (228 kB). Con Mis voces (lista, detalle, tarjetas, diálogos y hooks) y sus claves en los tres idiomas, el build llega a 230,45 kB.
- **Elegida**: subir el límite a 232 kB, con un margen de 1,5 kB sobre la medida, y dejar esta ficha como razón. La pantalla queda en el bundle principal, igual que la de Narración (ficha 006, que también se quedó dentro del presupuesto).
- **Descartadas**:
  - Importación diferida con `React.lazy`: el medidor suma el gzip de cada chunk por separado, y el total sube a 232,39 kB. Con este medidor no baja la cifra.
  - Quitar código o claves: no hay nada prescindible sin cambiar la pantalla.
  - Medir solo el JS de arranque en `budget.py`: cambia el significado de la etapa para todo el proyecto; va en PENDING `010-presupuesto-solo-arranque`.
- **Cómo revertir**: volver a 228 en `client/budget.json` cuando la etapa mida solo el JS de arranque (PENDING `010-presupuesto-solo-arranque`).
- **Cómo comprobarla**: `python -m devtools test-runner --type=budget` (límite 232 kB; medida 230,45 kB).
- **Pendiente**: la ficha PENDING `010-presupuesto-solo-arranque`.
