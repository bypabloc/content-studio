# 012: instalación de ffmpeg y Git con winget

- **Contexto**. El estudio utiliza ffmpeg y Git del sistema. WinGet puede registrar sus rutas mientras el estudio está abierto.
- **Elegida**. El trabajo de CPU usa los identificadores exactos de WinGet en el ámbito del usuario. La detección incorpora el PATH del registro y ejecuta el binario para declarar que está disponible.
- **Descartadas**. Incluir ffmpeg con la aplicación contradice el alcance del instalador. Cambiar el PATH persistente desde el estudio duplicaría el trabajo de WinGet.
- **Cómo revertir**. Revierte el grupo de detección e instalación de herramientas.
- **Cómo comprobarla**. Pruebas unitarias y de API con WinGet simulado. La corrida con WinGet real queda para la verificación final de la 012.

[Documentación de WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/install) · [Descarga de FFmpeg](https://ffmpeg.org/download.html) · [Instalación de Git](https://git-scm.com/install/)
