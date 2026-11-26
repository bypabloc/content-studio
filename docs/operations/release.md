# Publicar una versión del instalador

El instalador de Windows (NSIS, por usuario y en español) sale del workflow [release.yml](../../.github/workflows/release.yml) en el push de un tag `vX.Y.Z` (spec 022). La app instalada consulta `latest.json` del último Release y se actualiza sola.

## Requisitos (una vez)

* El par de claves del updater: la pública está en `plugins.updater.pubkey` de `client/src-tauri/tauri.conf.json`; la privada, en `~/.tauri/content-studio.key` del equipo del usuario, nunca en el repo. Si se pierde, las versiones instaladas no aceptan más actualizaciones: hay que generar otro par (`bun run --cwd client tauri signer generate -w ~/.tauri/content-studio.key`), cambiar la `pubkey` y reinstalar a mano una vez.
* Los secrets del repo `TAURI_SIGNING_PRIVATE_KEY` (el contenido de la clave privada) y `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` (vacío si la clave no tiene contraseña). Cargarlos lo hace el usuario: `gh secret set TAURI_SIGNING_PRIVATE_KEY < ~/.tauri/content-studio.key`.

## Pasos

1. En una rama `release/x.y.z` desde `dev`: `python -m devtools version x.y.z` (escribe la versión en los manifiestos y los locks), commit y PR a `dev`.
2. Con el usuario de acuerdo, PR de `dev` a `main` y merge (`git-workflow.md`).
3. Tag en `main` y push del tag: `git tag vX.Y.Z origin/main && git push origin vX.Y.Z`. Los tags no son ramas protegidas.
4. El workflow comprueba que el tag es la versión de los manifiestos (si no, falla en el primer paso), arma `uv.exe`, el server y los datos (`python -m devtools bundle`), compila con `tauri build --config src-tauri/tauri.bundle.json`, arma `tmp/release/` (`python -m devtools release`: instalador, firma, `latest.json` y notas) y publica el Release.

## Probar sin publicar

`gh workflow run release.yml --ref <rama> -f tag=vX.Y.Z -f dry-run=true` compila sin los secrets y deja el instalador como artefacto del run, sin crear el Release. Con un tag que no es la versión, falla en el primer paso.

En local, lo mismo a mano:

```bash
uv run --no-project python -m devtools bundle
bun run --cwd client tauri build --config src-tauri/tauri.bundle.json   # con TAURI_SIGNING_PRIVATE_KEY para la firma
uv run --no-project python -m devtools release --installer <target>/release/bundle/nsis/<exe> [--dry-run]
```

## Probar la app instalada

Instala fuera del checkout (en un checkout, la app arranca en modo desarrollo) y ábrela aislada con `app-check`:

```bash
"<instalador>.exe" /S /D=<carpeta fuera del repo>\app
python -m devtools app-check run --scenario=installed --binary=<carpeta>/app/content-studio.exe
```

`installed` exige la pantalla de preparación y la bienvenida; `updater` acepta una versión nueva servida desde un `latest.json` local (un build de prueba con `--config` que cambia `version` y `plugins.updater.endpoints`). Con `CONTENT_STUDIO_HOME`, la app, sus salidas y el borrado al desinstalar quedan en esa carpeta.

## Windows protegió tu PC

El instalador no tiene firma de código ([WARNING/publicar-v0.1.0](../process/WARNING/publicar-v0.1.0.md)): SmartScreen muestra «Windows protegió tu PC». Se sigue con **Más información** > **Ejecutar de todas formas**. Las notas de cada Release lo explican.

## Qué instala y qué conserva

* La app en `%LOCALAPPDATA%\Programs\Content Studio\` (con `uv.exe`, el server y los datos que se siembran); Python, el venv, los motores y la base en `%LOCALAPPDATA%\Content Studio\`, preparados en el primer arranque.
* Al desinstalar, los datos quedan. Con la casilla «Borrar los datos de la aplicación» y una confirmación más, se borran también `%LOCALAPPDATA%\Content Studio\` y `Documentos\Content Studio\`.
