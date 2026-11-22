# 015: masterización de la narración sobre `media/normalize.py`

**Qué queda.** La REFACTOR del ciclo 5 del plan: `narration/audio.py` (la masterización `--master voice`) repite la misma idea de dos pasadas de `loudnorm` que `media/normalize.py`. Migrarla debe conservar sus fixtures de caracterización; si cambian, va en un commit aparte.

**Por qué no se hizo.** La masterización usa TP -1,5, remuestreo a la frecuencia nativa (`aresample`) y su propia medición. Pasarla a `normalize.py` cambia la salida de la narración, así que no se mezcla con T5.

**Qué hacer.** Parametrizar `normalize.first_pass`/`second_pass` con el TP y el remuestreo, correr las pruebas de caracterización de la narración, y comparar la salida antes y después con `ebur128`.
