# 027: el instalador se compila pero no se firma (falta la clave del updater)

- **Qué**: `tauri build --config src-tauri/tauri.bundle.json` compila y arma el NSIS (`Content Studio_0.1.0_x64-setup.exe`, 17,02 MiB). Falla al firmar el updater: «A public key has been found, but no private key».
- **Por qué no bloquea la 027**: la clave privada es un secreto del usuario (`TAURI_SIGNING_PRIVATE_KEY`). La firma se hace al publicar (`docs/operations/release.md`).
- **Quién decide**: usuario.
- **Qué lo cierra**: publicar con la clave en el workflow de release (spec 022).
