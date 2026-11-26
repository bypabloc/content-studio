# HeartMuLa canta con el prompt instrumental de la app

- **Contexto**: la regla del proyecto es que la música sea siempre instrumental. Con el prompt instrumental de la app, HeartMuLa genera voz en las dos revisiones probadas (demucs mide la voz por encima de -25 dB). ACE-Step no tiene ese problema.
- **Elegida**: ninguna todavía. Lo decide el usuario:
  - (a) quitar HeartMuLa de la música instrumental (registro y receta),
  - (b) que el agente pruebe otros tags o un prompt sin sección de voz y mida con demucs, o
  - (c) dejarlo con un aviso.
- **Descartadas**: decidir sin el usuario, porque implica quitar un motor.
- **Cómo revertir**: no aplica.
- **Cómo comprobarla**: una pista de 30 s con la voz por debajo de -25 dB, o el motor fuera de `music/engines/registry.py`.
