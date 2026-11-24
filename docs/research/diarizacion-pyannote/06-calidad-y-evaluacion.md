# 06. Calidad y evaluación

## 1. DER publicado (leída, README de pyannote; actualizado en 2025-09)

DER en %, sin collar y contando el habla solapada (cuanto más bajo, mejor):

| Benchmark | 3.1 | **community-1** | precision-2 (nube, de pago) |
| :--- | ---: | ---: | ---: |
| AISHELL-4 | 12.2 | 11.7 | 11.4 |
| AliMeeting (canal 1) | 24.5 | 20.3 | 15.2 |
| AMI (IHM) | 18.8 | 17.0 | 12.9 |
| AMI (SDM) | 22.7 | 19.9 | 15.6 |
| AVA-AVD | 49.7 | 44.6 | 37.1 |
| CALLHOME (parte 2) | 28.5 | 26.7 | 16.6 |
| DIHARD 3 (completo) | 21.4 | 20.2 | 14.7 |
| Ego4D (dev.) | 51.2 | 46.8 | 39.0 |
| MSDWild | 25.4 | 22.8 | 17.3 |
| RAMC | 22.2 | 20.8 | 10.5 |
| REPERE (fase 2) | 7.9 | **8.9** | 7.4 |
| VoxConverse (v0.3) | 11.2 | 11.2 | 8.5 |

* community-1 mejora a 3.1 en 10 de 12 benchmarks, empata en VoxConverse y empeora en REPERE.
* Los peores casos son grabaciones «en la naturaleza» con muchas personas (AVA-AVD, Ego4D). Una entrevista o un pódcast de 2 a 4 personas con buen micrófono está más cerca de AMI IHM o VoxConverse: entre 11 y 17 %.
* Un usuario reportó que no logró reproducir el número de AliMeeting con 4.0.4 ([#1989](https://github.com/pyannote/pyannote-audio/issues/1989), título leído).

## 2. Español

* **No hay DER publicado de community-1 en español.**
* Benchmark independiente con pyannote 3.1 en CALLHOME español: **27,3 %**, contra 11,5 % en inglés. Usó collar de 0,25 s y contó los solapes. Por número de hablantes: 3,2 % con uno y 19,9 % con dos ([arXiv 2509.26177](https://arxiv.org/html/2509.26177v1), leída por el agente). CALLHOME es telefonía a 8 kHz con mucho solape: es un caso difícil y no representa un video con micrófono.
* Segmentación ajustada a CALLHOME español (`diarizers-community/speaker-segmentation-fine-tuned-callhome-spa`): pasó de 33,44 % a 25,72 % (snippet). Muestra que ajustar la segmentación por idioma o dominio sí mejora, pero es para 3.x y no lo necesitamos para empezar.
* Conclusión: la calidad en español **se mide con audios propios**.

## 3. Métricas

| Métrica | Mide | Para qué la usamos |
| :--- | :--- | :--- |
| **DER** | Tiempo mal atribuido: falsa alarma, voz perdida y confusión de hablante | La diarización sola, contra referencias RTTM. `pyannote.metrics` viene con pyannote |
| JER | Error de Jaccard por hablante: penaliza igual a un hablante con poco tiempo | Cuando importa no perder a quien habla poco |
| **WDER** | Fracción de palabras bien reconocidas con el hablante equivocado ([arXiv 1907.05337](https://arxiv.org/pdf/1907.05337)) | **La métrica de la integración** ([04](04-integracion-con-faster-whisper.md)) |
| cpWER | WER con la mejor permutación de hablantes | Transcripción y hablantes juntos |

## 4. Plan de evaluación propio (propuesta)

1. **Conjunto**: entre 6 y 10 clips de 2 a 10 min, con permiso de sus dueños. Por ejemplo:
   * una entrevista de 2 personas;
   * un pódcast de 3 o 4;
   * un diálogo rápido con interrupciones;
   * un clip con música de fondo;
   * un monólogo, para probar que no inventa hablantes;
   * dos voces del mismo género y edad.
2. **Referencia**: se anotan a mano los turnos (RTTM) y el hablante por palabra a partir del JSON de faster-whisper corregido. Una herramienta con línea de tiempo acelera esto. El editor del proyecto podría servir.
3. **Corridas**: community-1 en tres configuraciones, para ver cuánto ayuda fijar el número:
   * sin número de hablantes;
   * con `num_speakers` correcto;
   * con `min_speakers` y `max_speakers`.

   Asignación normal contra exclusiva, con y sin realineado por puntuación.
4. **Medir**: DER (sin collar y con collar de 0,25 s), WDER, VRAM pico y tiempo.
5. **Decidir** con números: qué salida usar, si el realineado se queda y qué valor de `embedding_batch_size`.
6. Los resultados van a una sección «Pruebas en GPU» de esta investigación, como hizo [la investigación de VoiceStudio](../voicestudio-narracion/13-pruebas-en-gpu.md).

## 5. Consejos de calidad (comunidad y código)

* **Fijar el número de hablantes** cuando se sabe: es lo que más evita fusionar voces ([03](03-api-y-uso.md) §3).
* **No separar la voz con Demucs antes de diarizar** salvo que haya música fuerte: no hay evidencia de que mejore con community-1, y suma otro modelo a la GPU (**no verificado**).
* **El preprocesamiento a 16 kHz mono no cambia el resultado**: pyannote ya lo hace al cargar. Sí ahorra decodificación y memoria (leída, tarjeta).
* **Solapes**: community-1 los detecta en la salida normal, pero en un caso real con 2 personas que se pisaban mucho, los tramos solapados quedaron asignados a uno solo ([#1987](https://github.com/pyannote/pyannote-audio/issues/1987), leída, sin resolver). Conviene no prometer nada sobre el habla simultánea.
* **Monólogos**: con un solo hablante, el DER del benchmark independiente fue 3,2 % (3.1). Si la UI sabe que habla una sola persona, se pasa `num_speakers=1` o directamente no se diariza.
