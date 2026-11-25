# 025: escucha de las salidas de AC-7

- **Qué**: la escucha es del usuario. Mediciones: `tmp/spec-025/mediciones.md`.
  - Música: `out/music/2026-11-24-2-lofi-chill/heartmula-lofi-chill.wav` (30 s, −11,6 LUFS, pico −0,9 dBFS). Sin silencios ≥0,25 s a −50 dB, pero el espectrograma muestra una caída de energía entre 10,3 y 11,1 s, cambios de sección hacia 3, 14, 20 y 26 s, y un corte de banda hacia 16 kHz. Confirmar que no hay voz y que las caídas son musicales.
  - Narración: `out/narration/2026-11-24-1-prueba-de-la-spec-025/qwen-0.6b-expert.wav` (1,82 s, −16,0 LUFS). Confirmar el gusto del acento y la pronunciación.
- **Por qué no se decide aquí**: el gusto lo decide el usuario (`verify-before-claiming-done.md` §2).
- **Cuándo**: después del merge a `dev`; no bloquea.
- **Quién**: usuario.
- **Qué lo cierra**: la escucha, con su resultado en la ficha.
