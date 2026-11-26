# 032: La red local es un segundo listener con TLS, apagado por defecto, que se enciende y se apaga sin reiniciar el server

- **Contexto**: D-1 pide un listener aparte en la IP elegida y el puerto 41831. La spec no dice si activarlo exige reiniciar el server compartido.
- **Elegida**: `LanListener` (`server/src/content_studio/lan/server.py`) levanta un segundo `uvicorn.Server` en un hilo del mismo proceso, con la app que arma `create_app(..., remote=True)`. `PUT /lan/settings` lo aplica al momento. Reserva el socket antes de arrancar, así un puerto ocupado da `lan_port_busy` (409) y deja `api.lan.enabled` en falso. La app de la LAN no lleva `HostGuard`: todas sus rutas exigen el token del dispositivo en un header (salvo `/pair`, que exige el PIN) y Tailscale Serve reenvía con otro Host.
- **Descartadas**: abrir el listener local a `0.0.0.0` (mezcla clientes de confianza y remotos). Exigir reiniciar el server para activarla (la app tendría que matar trabajos en curso).
- **Cómo revertir**: quitar `LanListener` de `cli/serve.py` y la rama `remote` de `create_app`.
- **Cómo comprobarla**: `uv run pytest server/tests/integration/test_lan.py -q` (AC-1, AC-2, AC-7, AC-11).
