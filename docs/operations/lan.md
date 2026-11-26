# Red local: usar Content Studio desde otro equipo

Un celular u otra PC de la misma red puede subir archivos, pedir trabajos (también por MCP) y descargar sus resultados. No tiene acceso a los archivos ni a la administración de esta PC. Está apagado por defecto (spec 032).

## Activar

1. En la app, **Ajustes > Integraciones > Red local**, activa «Permitir que otros equipos de mi red usen Content Studio».
2. Windows pide permiso de administrador (UAC) para crear la regla «Content Studio LAN» del firewall, solo para redes **privadas**. Si lo rechazas, la red local queda apagada.
3. Elige la **dirección en la red** (la IPv4 privada del Wi-Fi o del cable). La app muestra la URL (`https://<ip>:41831`) y la **huella del certificado**.

El server escucha en esa IP y el puerto 41831 (`api.lan.port`), con TLS y un certificado autofirmado que se crea una vez junto a la base (`lan-cert.pem`). La API local de `127.0.0.1:41830` no cambia. Con «mantener encendido» (`api.lan.keep_awake`, activo por defecto) el server no se apaga por inactividad mientras la red local esté activa.

Al desactivarla, el listener se apaga y la regla del firewall se borra.

## Emparejar un dispositivo

1. En la app, pulsa **Emparejar dispositivo**: aparece un PIN de 6 dígitos que vale 5 minutos y un solo uso. Cinco intentos fallidos lo anulan; genera otro.
2. Desde el dispositivo:

```bash
curl -k -X POST https://<ip>:41831/pair -H "Content-Type: application/json" -d '{"pin":"123456","name":"celular"}'
# {"client_id": 1, "token": "...", "fingerprint": "AB:CD:..."}
```

3. Comprueba que la `fingerprint` es la misma que muestra la app. Desde ahí, fija ese certificado o esa huella en el cliente (`-k` solo para el primer contacto).
4. Guarda el `token`: no se vuelve a mostrar. Si se pierde el dispositivo, **Revocar** en la app; su próxima petición da 401.

## Qué puede hacer un dispositivo

| Ruta | Para qué |
| :--- | :--- |
| `GET /health`, `GET /catalog/{narration,music,media}`, `GET /voices/profiles` | Leer el catálogo |
| `POST /uploads?name=voz.wav` (cuerpo: el archivo crudo) | Subir una entrada; devuelve `upload:<id>`. Tope: `api.lan.max_upload_mb` (2048), si no, 413 |
| `POST /jobs` | Pedir `narration`, `music`, `media.convert`, `media.normalize` o `clean.analyze`. Las entradas van como `upload:<id>`; una ruta de esta PC da 403 |
| `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/cancel`, `GET /jobs/{id}/outputs` | Solo sus trabajos |
| `GET /files?path=` | Descargar una salida de sus trabajos |
| `/mcp` | MCP por Streamable HTTP, con las herramientas de `studio mcp` menos `studio_watch_folder` |

Todo lo demás (motores, almacenamiento, ajustes, biblioteca, carpetas de entrada y emparejar) no existe en la red local (404).

```bash
TOKEN=...
curl -k -X POST "https://<ip>:41831/uploads?name=voz.wav" -H "Authorization: Bearer $TOKEN" --data-binary @voz.wav
curl -k -X POST https://<ip>:41831/jobs -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"kind":"media.convert","params":{"input":"upload:1","target":"mp3","options":{}}}'
curl -k https://<ip>:41831/jobs/7/outputs -H "Authorization: Bearer $TOKEN"
curl -k -o voz.mp3 "https://<ip>:41831/files?path=<ruta devuelta>" -H "Authorization: Bearer $TOKEN"
```

## MCP desde otra PC

```bash
claude mcp add --transport http content-studio https://<ip>:41831/mcp --header "Authorization: Bearer <token>"
```

El cliente debe confiar en el certificado autofirmado (por ejemplo, `NODE_EXTRA_CA_CERTS` apuntando a una copia de `lan-cert.pem`). En las herramientas, `input_path` y `script_path` son un `upload:<id>`. Un `Origin` distinto de la URL del listener da 403.

## Fuera de casa

Content Studio no se expone a internet. Para usarlo desde fuera, con [Tailscale](https://tailscale.com/kb/1312/serve) en esta PC y en el dispositivo:

```bash
tailscale serve --bg https+insecure://<ip>:41831
```

Así solo los equipos de tu tailnet lo alcanzan, con el mismo PIN y los mismos tokens.
