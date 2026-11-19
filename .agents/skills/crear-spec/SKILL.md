---
name: crear-spec
description: >
  Redacta una spec (plan de implementación) en docs/specs/ con el estándar del proyecto: Explore → Interview → Plan,
  copiando las plantillas de docs/specs/_plantilla/ (README, 01-contexto-y-decision, 02-plan,
  03-verificacion-final), con KISS, AC en BDD/EARS, ciclos TDD y verificación final. SIEMPRE invocar ANTES de diseñar
  un motor, un comando, un refactor mayor o un fix no trivial, y cuando el usuario pida "spec", "plan", "diseñar",
  "planificar", "desglosar", "roadmap de X", "lote de specs". La regla .agents/rules/plan-format.md es la fuente.
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(graphify:*), Bash(git log:*), Bash(git status:*)
argument-hint: "<qué se quiere lograr>"
---

# Crear una spec — content-studio

Fuente: `.agents/rules/plan-format.md`. Plantillas: `docs/specs/_plantilla/`. Índice: `docs/specs/README.md`.

## 1. Explore (sin escribir)

1. Lee las reglas del área (`codigo-python.md`, `stack.md`, `testing.md`) y el README de la herramienta (`narration/README.md`, `music/README.md`).
2. Ubica el código con graphify (`graphify query|explain|affected`) o `code-explorer`; mide el alcance real (cuántos archivos toca: decide la escala).
3. Revisa `docs/process/02-next/` (¿ya está pensada?), `WARNING/` y `PENDING/` (¿algo lo condiciona?) y las specs abiertas del índice (¿dependencias?).

## 2. Interview

- 1–4 preguntas por ronda con opciones concretas sacadas del código (AskUserQuestion). No preguntes lo que el código responde; si no hay dudas reales, dilo y pasa al plan.
- Decide tú lo técnico con la escalera KISS; pregunta lo que es del usuario: alcance, gusto sonoro, licencias para uso comercial, gasto.

## 3. Plan

1. `NN` = el siguiente libre de `docs/specs/README.md`; carpeta `docs/specs/<NN>-<slug>/` (lote: `docs/specs/<primera>-<última>-<tema>/`).
2. Copia las plantillas que pide la escala (Micro: solo `README.md`) y llénalas: reemplaza cada `<…>`, conserva los bloques fijos de decisiones y datos del usuario, borra las secciones que dicen «si aplica» y no aplican.
3. Comprueba antes de entregar:
   - Cada AC es verificable con una prueba concreta y está cubierto por al menos un ciclo TDD.
   - «Fuera de alcance» no está vacío; nada de `TODO` ni «por confirmar».
   - Cada decisión `D-n` pasó la escalera (¿debe existir? ¿ya existe? ¿stdlib?).
   - La lista de commits deja verde ruff y pytest en cada uno.
   - Si toca audio: «debe sonar / no debe sonar» y las mediciones de la verificación final.
4. Agrega la fila al índice `docs/specs/README.md` y, si venía de `02-next/`, saca esa tarea en el mismo cambio.

## 4. Entrega

Rutas de los archivos creados, la escala, los AC y la rama propuesta. La implementación es otra skill: `execute-spec`.
