# 005: graphify no indexa client/src

- **Qué**: D-10 pedía que `graphify.md` indexara `client/src`. El grafo sigue cubriendo `server/src/` y `tests/`: el client (TypeScript) no entró y la regla dice lo que hay.
- **Por qué no se hizo**: añadir el client al grafo exige correr `graphify update .` con el grafo del principal, y eso es una escritura que pide la skill `graphify-ops` (no se corrió en el lote).
- **Cuándo**: después de publicar la 005; antes de la 006, que añade más TypeScript.
- **Quién**: agente, con la skill `graphify-ops`.
- **Qué la cierra**: `graphify query "<símbolo del client>"` devuelve un nodo de `client/src`, y `graphify.md` lista `client/src` en su alcance.
