# Integraciones y Llamadas

> Investigación del 2026-11-15. Cubre el directorio de integraciones de VoiceStudio, el flujo n8n de texto a voz, Twilio (contestar llamadas con una voz guardada), el agente de llamadas y los Workflows con borradores de llamada. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

Fuente principal: clon local del repo `debpalash/VoiceStudio` (commit `80b4594`, 2026-11-16). Rutas relativas a la raíz del repo.

---

## 1. Qué Es

- **Directorio de integraciones** (sidebar → Integrations): tarjetas solo para conectores con configuración real, cada una con snippet copiable. Entradas: Twilio, n8n, GitHub Container Registry, Docker, Model Context Protocol, OpenAI Agents, Claude Code, Cursor, Codex CLI y VoiceStudio API. Los íconos van empaquetados (abrir el directorio no hace peticiones). **(leída)** `docs/integration-directory.md`; registro en `electron/src/renderer/src/features/integrations/setup-registry.ts`.
- **n8n**: exporta un workflow manual (Manual Trigger + HTTP Request) que llama a `POST /v1/audio/speech` y devuelve WAV. **(leída)** `docs/integrations/n8n.md`, plantilla `electron/src/renderer/src/features/integrations/n8n-workflow.json`.
- **Twilio**: contesta llamadas a tu número Twilio con un saludo sintetizado localmente y cuelga. Apagado por defecto. **(leída)** `docs/integrations/twilio.md`.
- **Agente de llamadas**: hace o contesta una llamada y mantiene una conversación corta para cumplir una tarea ("reserva mesa para 2 el viernes a las 20"), con tu voz verificada o una voz diseñada. **(leída)** `docs/integrations/calls.md`, `docs/calls.md`; API en `backend/api/routers/calls.py`.
- **Workflows**: lienzo local con recetas (narración en lote, normalizar, transcribir, cambiar voz, traducir y narrar) y borradores de llamada que nunca marcan solos. **(leída)** `docs/calls.md` §"Workflows and Calls".

## 2. Cómo Se Usa

### 2.1 n8n

1. Con VoiceStudio abierto y un motor TTS listo, **Integrations → n8n → Save as…** guarda `voicestudio-n8n.json`.
2. Importarlo en n8n y editar `input` en el nodo **VoiceStudio**. `voice: "default"` usa la voz del motor; para clonar, el id o nombre de un perfil.
3. Ejecutarlo a mano: el WAV queda en el campo binario `audio`.

Nodo exportado (extracto real) **(leída)** `n8n-workflow.json`:

```json
{
  "method": "POST",
  "url": "http://127.0.0.1:3900/v1/audio/speech",
  "jsonBody": "{ \"model\": \"tts-1\", \"input\": \"VoiceStudio\", \"voice\": \"default\", \"response_format\": \"wav\" }",
  "options": {
    "timeout": 1860000,
    "redirect": { "redirect": { "followRedirects": false } },
    "response": { "response": { "responseFormat": "file", "outputPropertyName": "audio" } }
  }
}
```

- n8n en Docker: `127.0.0.1` es el contenedor; usar `host.docker.internal` (Podman: `host.containers.internal`), que el backend acepta sin configurar `OMNIVOICE_ALLOWED_HOSTS`. **(leída)** `docs/integrations/n8n.md`.
- Backend protegido: HTTPS siempre fuera de loopback y credencial **Header Auth** `Authorization: Bearer <key>` en el gestor de n8n; nunca en la URL ni en el JSON. **(leída)** misma fuente.
- Probado por el autor con n8n 2.39.8 en Linux. **(leída)** misma fuente.

### 2.2 Twilio (saludo)

Pasos de la guía **(leída)** `docs/integrations/twilio.md`:

1. Account SID y Auth Token (se guardan cifrados y no se vuelven a mostrar).
2. Túnel HTTPS propio hacia el **listener de telefonía** (puerto 3950, no el 3900):
   ```sh
   cloudflared tunnel --url http://127.0.0.1:3950
   # o
   ngrok http 127.0.0.1:3950
   ```
3. En la consola de Twilio, webhook de voz `https://<túnel>/integrations/twilio/voice` (HTTP POST).
4. Elegir voz, motor y modo: **Play greeting** (≤ 1000 caracteres) o **AI agent**.
5. **Play phone-quality preview**: remuestrea a 8 kHz, codifica y decodifica μ-law, tal como lo oye quien llama; también pre-renderiza el saludo.
6. **Turn on calls**.

Cómo funciona: Twilio pide TwiML firmado → `<Connect><Stream>` con token de un solo uso (60 s) → el saludo se sintetiza **oración por oración** con el pipeline de TTS en streaming, se baja a 8 kHz μ-law y se envía en tramas de 20 ms (160 bytes) → `mark` → `<Hangup/>`. **(leída)** misma fuente.

### 2.3 Agente de llamadas

Requisitos (`GET /calls/readiness` → `credentials`, `tunnel`, `number`, `llm`, `asr`, `voice`) **(leída)** `docs/integrations/calls.md`:

- Twilio configurado y encendido, número de origen, un LLM en **Settings → LLM Providers** (local con Ollama/LM Studio para no sacar el texto de la máquina), un modelo ASR y una voz **verificada como propia** o **diseñada**. Clones de otras personas no pueden llamar (403 `voice_not_allowed`).

Flujo: marca → dice el aviso de IA (no interrumpible) → escucha con VAD por energía (700 ms de silencio cierra el turno) → transcribe → el LLM responde con `SAY:`, `ACTION: none|end_call|escalate` y `OUTCOME:` → se sintetiza desde la primera oración → si el interlocutor habla encima (~200 ms) el agente calla y envía `clear` a Twilio. Resultado: `booked`, `done`, `not_done`, `needs_you` o `failed`, con resumen y transcripción. **(leída)** misma fuente.

## 3. Opciones y Parámetros

Límites de Twilio, verificados contra el código **(leída)** `backend/services/telephony/config.py` l. 268-284 y `gateway.py` l. 28-50:

| Variable | Default | Rango |
| :--- | :--- | :--- |
| `OMNIVOICE_TWILIO_MAX_CALLS` | 2 | 1-16 |
| `OMNIVOICE_TWILIO_MAX_CALL_SECONDS` | 300 | 30-3600 |
| `OMNIVOICE_TWILIO_WEBHOOKS_PER_MINUTE` | 30 | 1-600 |
| `OMNIVOICE_TWILIO_PORT` | 3950 (o el siguiente libre) | — |
| `OMNIVOICE_TWILIO_HOST` | `127.0.0.1` | IP; en Docker `0.0.0.0` + publicar solo al túnel |

API del agente **(leída)** `docs/integrations/calls.md` y `backend/api/routers/calls.py` l. 40-257:

| Método y ruta | Uso |
| :--- | :--- |
| `POST /calls` | `{to, brief, profile_id, engine?, language?, disclosure?, max_minutes?}` → `201 {call}` |
| `GET /calls?limit=` | Historial |
| `GET /calls/{id}` | Registro con `transcript` y `timeline` |
| `GET /calls/{id}/events` | SSE: `status`, `transcript`, `agent_state`, `outcome`, `ended` |
| `POST /calls/{id}/say` | `{text}`: decir exactamente esto |
| `POST /calls/{id}/takeover` | `{enabled}`: pausa el LLM |
| `POST /calls/{id}/hangup` | Colgar |
| `DELETE /calls/{id}` | Borrar registro y grabación |
| `GET /calls/{id}/recording` | WAV estéreo (si se grabó) |
| `GET/PUT /calls/settings` | Admin: `from_number`, `disclosure_template`, `inbound_mode`, `max_concurrent`, `record_calls`, `allow_remote_control`… |
| `GET /calls/readiness`, `GET /calls/options` | Checklist y aviso renderizado |

CLI equivalente: `voicestudio calls start|list|show|events|say|takeover|hangup|readiness|configure|recording|delete`. **(leída)** `cli/voicestudio_cli/contracts.json`.

Workflows **(leída)** `docs/calls.md`: hasta 50 guiones de ≤ 20 000 caracteres, separados por una línea `---` o importados de TXT, MD, DOCX, PDF o EPUB; cada archivo es un clip. "Normalize audio" es normalización **de pico** (−24 a −1 dBFS, default −2), no LUFS.

## 4. Ejemplos

Llamada saliente por API (campos leídos; valores de ejemplo, **no verificado** en ejecución):

```bash
curl -X POST http://127.0.0.1:3900/calls -H 'Content-Type: application/json' \
  -d '{"to":"+14155550123","brief":"Reservar mesa para 2 el viernes a las 20:00","profile_id":"<voz-verificada>","max_minutes":5}'
curl -N http://127.0.0.1:3900/calls/<id>/events
```

Eventos SSE **(leída)** `docs/integrations/calls.md`:

```text
data: {"type":"agent_state","state":"listening"}
data: {"type":"transcript","speaker":"caller","text":"...","final":true,"t":4.2}
data: {"type":"outcome","outcome":"booked","summary":"..."}
```

Narración en lote desde Workflows (UI): **New from template → Batch narration**, pegar guiones separados por `---`, elegir voz, idioma y velocidad, **Run workflow**; exporta WAV con nombres numerados y seguros para el sistema de archivos. **(leída)** `docs/calls.md`.

## 5. Tips y Trucos

- **Nunca** apuntes el túnel al puerto 3900: publicarías toda la API. El listener 3950 solo sirve tres rutas y responde 404 al resto. **(leída)** `docs/integrations/twilio.md`.
- Los túneles rápidos cambian de URL al reiniciar; actualiza URL pública y webhook o fallará la firma. **(leída)** misma fuente.
- Grabar exige dos cosas: **Record calls** activado y un aviso que diga que la llamada se graba; si no, no graba. **(leída)** `docs/integrations/calls.md`.
- Un filtro aparte bloquea frases con números de tarjeta o números de 9+ dígitos que no estén en tu brief. **(leída)** misma fuente.
- El aviso de IA es editable y puede vaciarse, pero la responsabilidad legal es del usuario (TCPA en EE. UU., consentimiento de grabación). **(leída)** misma fuente.
- n8n: el timeout exportado es 31 min (1 860 000 ms) para cubrir carga de modelo + generación en CPU. **(leída)** `n8n-workflow.json`, `docs/integrations/n8n.md`.
- **conflicto (menor)**: `docs/agentic-voice.md` dice que las llamadas salientes son "un hito diferido", mientras `docs/integrations/calls.md` y `backend/api/routers/calls.py` ya implementan `POST /calls`. Vale el código.

## 6. Problemas Conocidos

| Issue | Estado | Resumen |
| :--- | :--- | :--- |
| [#2428](https://github.com/debpalash/VoiceStudio/issues/2428) | cerrado | El agente leía en voz alta el razonamiento de modelos que prellenan `<think>` (Qwen3 thinking, DeepSeek-R1) y lo guardaba en la transcripción. **(leída)** |
| [#2628](https://github.com/debpalash/VoiceStudio/issues/2628) | cerrado | Respuestas iniciales cortas dejaban activa la ventana de "primera cláusula". **(snippet)** solo título. |
| [#3811](https://github.com/debpalash/VoiceStudio/issues/3811) | cerrado | Pedido de permitir un proveedor LLM con credencial por HTTP plano en LAN de confianza. **(snippet)** |

- Plivo y Telnyx no están soportados. **(leída)** `docs/integrations/twilio.md`.
- Sin issues encontrados sobre n8n (búsqueda en GitHub sin resultados el 2026-11-16). La búsqueda de GitHub alcanzó el límite de tasa antes de terminar otras consultas; pueden faltar issues.

## 7. Qué Dice la Comunidad

- **B** — [andrew.ooo](https://andrew.ooo/posts/voicestudio-review-local-elevenlabs-alternative/) (sep-2026, updates nov): menciona llamadas Twilio con voz guardada, apagadas por defecto, y Docker/Colab como integraciones; no las prueba.
- **B** — [remio.ai](https://www.remio.ai/post/debpalash-voicestudio-hit-github-trending-but-local-voice-ai-still-has-to-prove) (sep-2026): advierte que traducción avanzada con LLM alojado puede sacar parte del flujo de la máquina, y que la marca de agua no equivale a control universal.
- No encontré tutoriales independientes (2025-2026) del flujo n8n ni del agente de llamadas. **no verificado**.

## 8. Qué Sirve para social-videos

- **Llamadas y Twilio: no aplican** a narración de videos. Descartar.
- **n8n: idea útil, sin código.** Si algún día se automatiza la producción (guion en Notion/Sheets → narración → música → render), basta con que `narration/tts.py` pueda llamarse desde un nodo "Execute Command" o exponer un contrato `POST /v1/audio/speech`. La plantilla de VoiceStudio enseña buenas prácticas: workflow inactivo y manual, sin credenciales en el JSON, timeout largo y sin seguir redirecciones.
- **Workflows "Batch narration": la idea más útil de este grupo.** Copiar el diseño en `tts.py`:
  1. Aceptar un archivo con varios guiones separados por `---` y generar un clip por bloque con nombres numerados y seguros (`01-intro.wav`, `02-…`).
  2. **Checkpoint por clip**: si falla el clip 7, reintentar desde ahí sin regenerar los anteriores; invalidar solo si cambia texto, voz, idioma, velocidad o modelo.
  3. Un paso opcional de normalización y dejar claro si es de **pico** o **LUFS** (para redes sociales conviene LUFS, ~−14 integrados; VoiceStudio solo hace pico).
- **Preview "calidad de destino"**: igual que el preview a 8 kHz μ-law de Twilio, se puede renderizar una vista previa como suena en el destino (p. ej. AAC 128 kbps de Reels/TikTok) para juzgar la voz antes de exportar. Implementable con ffmpeg.
- **Política de voces**: VoiceStudio solo deja "llamar" con voz propia verificada o diseñada. Encaja con la regla 5 de social-videos (clonar solo con permiso): un campo `consentimiento` en los metadatos de cada voz en `narration/voz/` sería un control barato.
