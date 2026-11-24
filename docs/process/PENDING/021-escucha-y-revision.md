# 021: escuchar la narración revisada y puntuar las traducciones del asistente

- **Qué**: la verificación de la 021 dejó, para el usuario, en `../content-studio-worktrees/retained/021-local-llm-assist/` (junto al checkout; el worktree ya se cerró):
  - La narración del guion de prueba, original y revisada con el ★: `out/narration/2026-11-24-5-expert/guion-voxcpm2.wav` (28,9 s) y `out/narration/2026-11-24-10-expert/guion-revisado-qwen-voxcpm2.wav` (35,3 s), las dos a -16,1 LUFS y -1,5 dBFS. El espectrograma de la revisada muestra pausas de corte seco (las `[pausa]` son silencio digital) y un posible clic hacia 17,6 s.
  - La pista `out/subtitles/2-tutorial-agenda.pt.srt` (42 cues traducidos al portugués) y las 10 traducciones por modelo de los informes de `llm-eval` (`tmp/llm-eval/`), para puntuar de 1 a 5.
  - La música de 30 s desde «algo tranquilo con piano y lluvia para un tutorial de cocina»: `out/music/2026-11-24-8-gentle-piano-rain-ambience-subtle-pads-c/` (-18,6 LUFS, sin voz según demucs).
- **Por qué no se hizo**: el gusto y la calidad de la traducción los decide el usuario (`verify-before-claiming-done.md`).
- **Cuándo**: antes de publicar el lote.
- **Quién**: usuario.
- **Qué la cierra**: la escucha y la puntuación; si Gemma gana claro en la traducción, se cambia el ★ (WARNING [021-recomendado](../WARNING/021-recomendado.md)).
