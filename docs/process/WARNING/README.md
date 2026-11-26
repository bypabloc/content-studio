# Decisiones y lo que se revisa antes de pasar a `main`

Aquí va cada decisión que un agente tomó solo al ejecutar una spec (la opción correcta, no la más rápida) y todo lo que hay que aplicar o revisar **antes** de publicar en `main`: un venv nuevo que instalar, un modelo que descargar, una licencia que confirmar para uso comercial, un paso manual. Cada ficha se borra al aplicarla, en un PR a `dev`, con su fila. Lo que se revisa **después** va en [`../PENDING/`](../PENDING/README.md).

Nombre: `<spec>-<tema>.md` (sin spec, `<tema>.md`). Formato:

```markdown
# <spec>: <decisión en una línea>

- **Contexto**: qué se encontró y por qué hubo que elegir.
- **Elegida**: la opción y su motivo (la correcta, no la más rápida).
- **Descartadas**: cada alternativa y por qué no.
- **Cómo revertir**: commit o pasos para volver atrás.
- **Cómo comprobarla**: comando o prueba que la confirma.
- **Pendiente**: ficha de `../PENDING/` si deja trabajo para después.
```

| Ficha | Qué | Antes de |
| :--- | :--- | :--- |
| [firma-y-traducciones](firma-y-traducciones.md) | Firma de código del instalador (SmartScreen) y revisión humana de `en.json` y `pt.json` | Difundir el instalador |
| [verificacion-app-instalada](verificacion-app-instalada.md) | Instalar encima, actualizar desde una versión anterior, UAC y red local desde otro equipo, inicio con Windows y hablantes con un clip real | `main` |
| [licencias-indextts-omnivoice](licencias-indextts-omnivoice.md) | IndexTTS y OmniVoice sin verificar hasta que se acepte su licencia no comercial | `main` |
| [heartmula-canta](heartmula-canta.md) | HeartMuLa genera voz con el prompt instrumental: quitarlo, seguir probando o avisar | `main` |
