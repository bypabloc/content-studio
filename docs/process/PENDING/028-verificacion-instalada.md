# 028: verificación con la app instalada y con una versión anterior

- **Qué**: dos comprobaciones de la 03 que no se hicieron en este equipo. (a) AC-9: con una versión anterior instalada, actualizar y comprobar que el server viejo se detiene y arranca el nuevo (`app-check run --binary=<instalador>`, escenario de actualización). (b) Reactivación desde la ventana real: con `api.idle_minutes` = 1, la app abierta sobre un server apagado por inactividad reconecta al generar algo.
- **Por qué no se hizo**: no hay un instalador de una versión anterior en este equipo, y la reactivación real exige operar la ventana (app-check no tiene escenario para eso). Quedan cubiertas en pruebas: AC-9 en `cargo test` (`restarts_server_of_other_version`, `stop_*`) y la reactivación con e2e de API simulada (`happy-server-wakes`).
- **Cuándo**: antes de publicar en `main`.
- **Quién**: usuario y agente.
- **Qué la cierra**: `python -m devtools app-check run --binary=<instalador anterior>` con el escenario de actualización en verde, y una corrida manual de (b) anotada en esta ficha.
