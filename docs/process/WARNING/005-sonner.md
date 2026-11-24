# 005: sonner para los toasts (dependencia nueva)

- **Contexto**: al terminar un trabajo hay que avisar con un toast que tenga «Abrir carpeta» (AC-5), sin escribir un sistema de avisos propio.
- **Elegida**: `sonner` 2.0.8 (versión exacta). Es el toast que la referencia audio-converter ya usa; el `Toaster` va en `Shell.tsx`.
- **Descartadas**: un toast hecho a mano (más código y accesibilidad a cargo nuestro); `react-hot-toast` (otra dependencia para lo mismo).
- **Cómo revertir**: quitar `sonner`, cambiar `tauriAlerts.toast` (`client/src/shared/notify/alerts.ts`) por un componente propio y quitar el `Toaster`.
- **Cómo comprobarla**: `cd client && bun run test` (incluye `tests/unit/src/shared/notify/alerts.test.ts`).
- **Antes de**: el merge a `dev`.
