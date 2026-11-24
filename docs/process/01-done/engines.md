---
modulo: Motores y almacenamiento
actualizada: 2026-11-21
---

# Motores y almacenamiento

## Qué resuelve

Instala y administra los motores bajo demanda, conserva aislados sus entornos y permite elegir dónde guardar modelos y salidas.

## Qué hace hoy

El catálogo ofrece nueve recetas fijadas, instalaciones reanudables, verificación de humo, reparación y desinstalación según propiedad. Detecta FFmpeg, Git y GPU; en Windows puede ofrecer instalar FFmpeg o Git con winget. Ajustes > Almacenamiento mueve motores o salidas con verificación y la bienvenida guía el primer uso.

## Dónde vive

El código está en `server/src/content_studio/engines/`, `storage/`, `system/` y `services/`. Las recetas viven en `engines/recipes/`. `paths.engines_dir()` resuelve la carpeta elegida; el valor predeterminado es `%LOCALAPPDATA%\Content Studio\engines` en Windows y `~/.local/share/content-studio/engines` en POSIX. Las voces y referencias siguen en `server/data/`.

## Historial

- 2026-11-21: Motores, almacenamiento elegible, bienvenida y herramientas del sistema (spec 012; PR pendiente).
