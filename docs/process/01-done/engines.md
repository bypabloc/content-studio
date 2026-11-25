---
modulo: Motores y almacenamiento
actualizada: 2026-11-25
---

# Motores y almacenamiento

## Qué resuelve

Instala y administra los motores bajo demanda, conserva aislados sus entornos y permite elegir dónde guardar modelos y salidas.

## Qué hace hoy

El catálogo ofrece nueve recetas fijadas, instalaciones reanudables, verificación de humo, reparación y desinstalación según propiedad. Detecta FFmpeg, Git y GPU; en Windows puede ofrecer instalar FFmpeg o Git con winget. Ajustes > Almacenamiento mueve motores o salidas con verificación y la bienvenida guía el primer uso.

## Dónde vive

El código está en `server/src/content_studio/engines/`, `storage/`, `system/` y `services/`. Las recetas viven en `engines/recipes/`. `paths.engines_dir()` resuelve la carpeta elegida; el valor predeterminado es `%LOCALAPPDATA%\Content Studio\engines` en Windows y `~/.local/share/content-studio/engines` en POSIX. Las voces y referencias siguen en `server/data/`.

## Versiones y huella (spec 026, 2026-11-25)

- La huella de una receta es el sha256 de sus bytes en disco; en este equipo (`autocrlf=true`) las recetas van en CRLF.
- Un intento de instalación fallido ya no reutiliza pasos ni venv de la receta anterior: si la huella del intento pendiente no coincide, se rehace todo (commit `9d96a1a`).
- Motores de transcripción (faster-whisper, 3.14) y visión (vision, 3.15) verifican su librería; el caso de «Verificar» en Motores para sus familias falta (ficha `026-verificacion-familias`).
- Las instalaciones externas del usuario (indextts, omnivoice en el checkout principal) no se tocaron.
- Motores restringidos (pyannote, spec 034): su tarjeta pide el token de Hugging Face, lo guarda sin mostrarlo y deja Instalar deshabilitado sin él. El token se pasa solo al entorno del paso `hf` restringido; un 401 o 403 de Hugging Face sale con código 25 (`engine_gated`).

## Historial

- 2026-11-21: Motores, almacenamiento elegible, bienvenida y herramientas del sistema (spec 012; PR pendiente).
- 2026-11-25: Diarización con pyannote: receta, token de Hugging Face en Motores y atribución en Acerca de (spec 034).
