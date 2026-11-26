# 032: Activar la red local en la app instalada, aceptar el UAC y ver la regla del firewall

- **Qué**: 03 §2, paso 1 (AC-9 real): con la app instalada, activar la red local, aceptar el aviso de UAC y comprobar con `netsh advfirewall firewall show rule name="Content Studio LAN"` que la regla existe solo para el perfil Privado. Al desactivar, que se borra. Rechazar el UAC debe mostrar el aviso y dejar la red local apagada.
- **Por qué no se hizo**: el aviso de UAC lo acepta una persona; `app-check` no lo maneja y Computer Use está prohibido. Hay pruebas del comando armado y del rechazo (`cargo test … firewall`), y e2e con el comando simulado (`neg-lan-firewall-declined`).
- **Cuándo**: antes de publicar en `main`.
- **Quién**: usuario.
- **Qué la cierra**: la regla vista con `netsh` tras activar, y su ausencia tras desactivar.
