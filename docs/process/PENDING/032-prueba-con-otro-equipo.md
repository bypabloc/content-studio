# 032: Probar la red local desde un celular u otra PC real, y el MCP por HTTP desde un cliente de otra PC

- **Qué**: 03 §2, pasos 2 y 3: emparejar, subir, convertir y bajar desde otro equipo de la red, y conectar Claude Code (`--transport http`) desde otra PC para listar herramientas y narrar.
- **Por qué no se hizo**: en la sesión no había otro equipo. Se probó lo mismo contra la IP privada real de esta PC (`192.168.18.67:41841`) con un server aislado, como si fuera otro dispositivo: emparejar (huella igual a la de la app), PIN reusado 401, token local 401, `/engines` 404, ruta de esta PC 403, subida, `media.convert` con `upload:1` (MP3 de 3,03 s), descarga, revocar 401 y desactivar con el puerto cerrado. El MCP HTTP se probó con el cliente del SDK sobre TLS real en `test_lan.py::test_ac8_*`.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: usuario (el dispositivo) y agente.
- **Qué la cierra**: la secuencia de `docs/operations/lan.md` desde el celular u otra PC, y `claude mcp add --transport http …` desde otra PC con una narración que termine.
