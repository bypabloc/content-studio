# 026: heartmula canta con el prompt instrumental de la app (en ambas revisiones)

- **Contexto**: en la prueba de 30 s con `lofi-chill`, demucs (la evaluación de voz de la app, `music/evaluation.py`) detecta voz: -2,4 dB respecto a la mezcla con la revisión nueva y -1,3 dB con la anterior (umbral -25 dB). ACE-Step en la misma prueba: -42,4 dB. El motor manda `[Intro]`, `[Instrumental]` y el tag `instrumental`, y el modelo canta igual.
- **Elegida**: dejar HeartMuLa en la lista de motores con la revisión anterior, pero marcar que su música **no cumple** la regla «siempre instrumental» (reglas críticas de la spec 026). No se marca como verificado para música instrumental.
- **Descartadas**: declarar HeartMuLa instrumental sin medirla; quitar el motor de la app (la decisión es del usuario, no del agente).
- **Cómo revertir**: no aplica hasta que haya un prompt o una revisión que dé voz -25 dB o menos.
- **Cómo comprobarla**: `tmp/spec-026/checks/voice_check.py` con el Python del venv de ACE-Step sobre la pista (la app solo evalúa con `--evaluate` en el venv de ACE-Step).
- **Pendiente**: [026-heartmula-voz](../PENDING/026-heartmula-voz.md).
