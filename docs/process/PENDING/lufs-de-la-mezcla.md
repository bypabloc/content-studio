# 016: las mezclas con picos quedan bajo el objetivo de -14 LUFS

- **Qué**: AC-3 de la 016 pide -14 ± 0,5 LUFS con TP ≤ -1 dBTP. Las mezclas reales quedan en -14,7 y -14,8 LUFS, y el video `replace` en -15,6 LUFS. La normalización lineal reduce la ganancia para respetar el techo de pico.
- **Por qué no se hizo**: hay tres caminos y es una decisión del usuario:
  1. Iterar un limitador sobre el crudo hasta cumplir; no está probado.
  2. Aceptar ±1,5 LU en las mezclas con picos.
  3. Dejarlo como está.
- **Cuándo**: cuando el usuario escuche una mezcla.
- **Quién**: usuario (decide) y agente (implementa la 1 si se elige).
- **Qué la cierra**: la decisión. Las mediciones y el experimento están en el historial de git de esta ficha (antes `016-lufs-real-fuera-de-ac3.md`). El código vive en `mix/render.py` y `media/normalize.py`.
