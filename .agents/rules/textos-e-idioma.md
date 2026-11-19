---
trigger: always_on
description: Idioma del código, de los textos del CLI, de la documentación y de la narración (español neutro latinoamericano, tuteo)
---

# Textos e idioma — SIEMPRE ACTIVA

content-studio es un proyecto en español de punta a punta: hay un solo idioma, así que **no hay catálogo i18n** (sería una abstracción sin segundo uso; `plan-format.md` §0). Lo que sí es obligatorio es la consistencia:

| Qué | Idioma y forma |
| :--- | :--- |
| Identificadores, módulos y carpetas de código | Español, sin tildes ni ñ (`relanzar`, `usar_venv`, `EspecMotor`, `turno_gpu`). Términos técnicos consolidados en inglés si no tienen equivalente natural (`venv`, `parser`, `prompt`) |
| Mensajes del CLI, ayuda de Typer, errores y logs visibles | Español neutro latinoamericano, con tuteo (nunca voseo ni formas peninsulares), cortos y accionables: qué falló y qué hacer (`Falta narration/.venv-qwen. Ver la instalación en narration/README.md.`) |
| Docstrings, comentarios, README, docs, reglas y specs | Español neutro; los comandos y rutas tal cual |
| Commits y PRs | Conventional Commits en español (`git-workflow.md`) |
| Etiquetas de `PROGRESS.md` del handoff | En inglés (`Status`, `Phase`, `Next step`): las lee el mod; sus valores, en español |
| Narración generada | Español neutro latinoamericano, salvo que se pida otro idioma; el texto se normaliza por motor (`narration/texto/`) |
| Nombres de estilos y presets de música | Los del catálogo (`music/estilos.py`), en kebab-case |

* Un texto visible repetido en varios lugares se define una vez en su módulo (p. ej. las descripciones de motores en `registro.py`), no se copia.
* No mezcles idiomas dentro de un mismo mensaje.
