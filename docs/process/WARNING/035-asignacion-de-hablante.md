# 035: asignación de hablante, casos que la spec no fija

- **Contexto**: AC-1 fija el solape, el hueco de 1 s y el caso lejano, pero no una palabra sin `end` ni un empate de solape ni cómo medir un hueco.
- **Elegida**: una palabra sin `end` cuenta como un instante (`end = start`); en empate de solape gana el primer turno de la lista; la distancia a un turno es `max(0, inicio del turno - fin de la palabra, inicio de la palabra - fin del turno)`, y entra si queda en `max_gap` o menos.
- **Descartadas**: descartar la palabra sin `end` (perdería la palabra en la unión); repartir el empate (no hay un hablante correcto); medir el hueco al punto medio (la distancia al borde es lo que pide AC-1).
- **Cómo revertir**: cambiar `_speaker_at` en `server/src/content_studio/diarization/assign.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/diarization/test_assign.py -q`.
- **Pendiente**: ninguno.
