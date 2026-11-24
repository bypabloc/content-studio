# 019: client-unit bajo carga

- **Qué**: las corridas completas siguen fallando por timeouts. La última dio 1528/1534; fallaron UISelect, MixPage, ReframePreview (2), Shell y EditorWorkspace. `Shell.test.tsx` pasa 15/15 aislado; `SubtitlesEditor.test.tsx` pasa 12/12.
- **Por qué no se hizo**: los casos aislados pasan y los fallos cambian entre corridas. `vmThreads` dio 1528/1534; `threads`, 1507/1534 y 259 workers. Se conserva `forks`, seis workers y `testTimeout` de 5 s.
- **Cuándo**: antes de cerrar 019; repetir `python -m devtools test-runner --type=client-unit` y el hook completo.
- **Quién**: agente.
- **Qué la cierra**: una corrida completa de client-unit y el hook de commit pasan; borrar esta ficha y su fila.
