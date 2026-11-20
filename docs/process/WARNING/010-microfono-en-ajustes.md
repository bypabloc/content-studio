# 010: el micrófono se elige en Ajustes y la grabación lo usa

- **Contexto**: el usuario no sabía qué micrófono usaba la app y pidió poder ver la lista y elegir uno.
- **Elegida**: sección «Micrófono» en Ajustes con el botón «Ver micrófonos». La lista sale al pulsarlo, no al abrir la pantalla, porque listar abre el micrófono un instante. La elección se guarda en `select.recording.microphone` (vacía = predeterminado de Windows). El asistente y la prueba de sala la pasan a `getUserMedia` como `exact`. «Restablecer elecciones» la borra, porque su clave va bajo `select.`.
- **Descartadas**: listar al abrir Ajustes (abriría el micrófono sin que el usuario lo pida); pedir el dispositivo sin `exact` (una elección que ya no existe caía al predeterminado sin avisar).
- **Por qué `exact`**: si el micrófono elegido se desconecta, la grabación falla con el aviso de error. Así no se graba con otro micrófono sin que el usuario lo sepa.
- **Cómo revertir**: quitar la sección de `SettingsPage` y el `deviceId` de `useRecorder` (volver a `deviceId` sin `exact`, o quitar el parámetro).
- **Cómo comprobarla**: `microphones.test.ts`, `MicrophonePicker.test.tsx`, `useRecorder.test.ts` (AC-3, con `exact`) y la prueba «graba con el micrófono que se eligió» de `RecordWizard.test.tsx`. Con un micrófono real: PENDING `010-grabar-con-microfono-real`.
- **Nota**: Windows oculta los nombres de los micrófonos hasta que uno se abre. `listMicrophones` abre uno un instante para obtenerlos y lo suelta enseguida.
