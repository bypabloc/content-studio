# 030: la prueba de axe en inglés y portugués de happy-language falla a veces en la suite completa

- **Qué**: `tests/e2e/settings/happy-language.e2e.ts` (axe sin fallos serios en inglés y portugués) falló en 4 de 5 corridas completas de la suite, con 58 violaciones de contraste. Aislada pasa, y `tests/e2e/settings` pasa 13 de 13.
- **Qué se cambió**: antes de cada análisis, la prueba desactiva transiciones y animaciones con un estilo (`addStyleTag`). Después, en 8 corridas completas, falló 1 vez (2 pruebas, sin identificar). Esperar a que no corra ninguna animación no sirvió: hay animaciones infinitas (esqueletos, progreso) y la espera caducaba.
- **Por qué no se cierra**: no hay evidencia de que la sección de carpetas de entrada lo cause; las violaciones no apuntan a sus elementos. Sin reproducir el fallo en la base de `dev`, no se puede afirmar que es anterior.
- **Cuándo**: después de publicar 030, o antes si el pre-push se cae por una prueba de e2e.
- **Quién**: agente.
- **Qué lo cierra**: cinco corridas completas seguidas sin fallos, o la identidad de las dos pruebas de la corrida que falló.
