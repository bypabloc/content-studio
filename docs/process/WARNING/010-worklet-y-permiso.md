# 010: el worklet se carga con `?worker&url`; el permiso del micrófono se prueba en la app

- **Contexto**: `AudioWorklet` necesita la URL de un script. `new URL('./x.ts', import.meta.url)` no transpila TypeScript, y un Blob con el código exigiría `blob:` en la CSP de la ventana. Vite ofrece `?worker&url` y el tsconfig carga `vite/client`, que lo tipa.
- **Elegida**: `import workletUrl from '…/recorder-worklet.ts?worker&url'`. El worklet no tiene imports y declara `AudioWorkletProcessor` a mano, porque el DOM de TypeScript no lo trae. Lleva `export {}` para ser módulo (su test lo importa). oxlint marca el `default` de ese import, que es la URL de Vite: la directiva `oxlint-disable-next-line` va en `useRecorder.ts`, con su razón.
- **Descartadas**: Blob con código inline (CSP); `ScriptProcessorNode` (obsoleto y corre en el hilo principal).
- **Cómo revertir**: cambiar la importación por un Blob con el código del worklet y ajustar la CSP en `src-tauri`.
- **Cómo comprobarla**: `recorder-worklet.test.ts` ejecuta el procesador con una clase base falsa (copia de cada bloque, entrada vacía). La prueba del hook usa un AudioContext falso, así que no ejecuta el worklet real. Se mira en la app (`bun run --cwd client tauri dev`) al grabar en el ciclo 7; el e2e `recording/happy-record-take` usa el micrófono simulado de Chromium.
- **Pendiente**: el permiso del micrófono en WebView2 (`src-tauri`). D-2 prevé el handler de `PermissionRequested` si la ventana no lo pide; se decide en el ciclo 7, probado en la app.
