# 032: Dependencia nueva explícita: cryptography para generar el certificado autofirmado

- **Contexto**: la stdlib no genera certificados X.509 (D-4). `cryptography` ya venía como dependencia transitiva de `mcp`.
- **Elegida**: declararla en `server/pyproject.toml` (`cryptography>=50.0.2`, Apache 2.0 o BSD), importada solo dentro de `lan/cert.py::ensure`. El certificado es EC P-256, válido 10 años, con la IP elegida en el SAN. Se crea una vez junto a la base (`lan-cert.pem`, `lan-key.pem`) y no se rehace al cambiar de dirección: la huella fijada en los dispositivos sigue valiendo.
- **Descartadas**: HTTP sin cifrar (el token viajaría en claro por el Wi-Fi). `mkcert`, que obliga a instalar una CA en cada dispositivo. Llamar a `openssl`, que Windows no trae.
- **Cómo revertir**: `uv remove --project server cryptography` y volver a TLS desactivado (no recomendado).
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/lan/test_cert.py -q`.
