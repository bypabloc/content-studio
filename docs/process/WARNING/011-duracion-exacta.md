# 011: duración exacta de la música: cuánto se pide y cómo se corta

- **Contexto**: ACE-Step termina antes de lo pedido y rellena con silencio. El recorte deja la pista corta (30 s pedidos dieron 22,5 s). La spec pide que la pista final dure lo pedido, con un fade al final.
- **Elegida**: `music/duration.py`. `plan_duration(target, max)` pide `target` + 25 %, con un mínimo de +10 s, sin pasar el máximo del motor (`MusicSpec.max_seconds`: ACE 600, HeartMuLa 240). `finish(path, target)` recorta el silencio final y, si la pista alcanza el objetivo, la corta en `target` con un fade de 2 s (un tercio del objetivo si es menor de 6 s). Ambos motores la usan.
- **Curva del fade**: `hsin` (media sinusoide). Medido sobre un tono de 34 s: `lin` baja 16,8 dB en el último medio segundo, y no cumple el AC-2 (-20 dB). `exp` cae a silencio digital al final. `hsin` baja 23,6 dB, y la rampa es suave.
- **Dónde queda el recorte de silencio**: en `music/evaluation.py`, como hoy. La spec decía «si estaba suelto en `music_main.py`», pero no estaba ahí.
- **Descartadas**: el loop con crossfade (la spec ya lo descartó) y el «aproximado» de antes.
- **Pendiente de este grupo**: el reintento cuando la pista sale corta (AC-3) va en el siguiente grupo. Hasta entonces, una pista corta se devuelve tal cual, sin aviso.
- **Cómo revertir**: quitar `finish` y `plan_duration` de los motores (volver a `trim_silence` y `duration=a.duration`), y `MusicSpec.max_seconds`.
- **Cómo comprobarla**: `music/test_duration.py` (AC-1, AC-2, el fade de 4 s y `finish`) y los doctests de `duration.py`. En ACE-Step real, AC-9 (verificación final).
