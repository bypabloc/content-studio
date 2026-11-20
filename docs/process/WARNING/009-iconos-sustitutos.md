# 009: iconos sustitutos y el mapa de `UIIcon`

- **Contexto**: D-2 pide nombres de content-studio. La versión de lucide-react que fijó la 008 (1.58.0) no exporta `Stop` ni un icono de fotograma clave, así que hay que elegir sustitutos.
- **Elegida**: cada nombre de D-2 apunta a un icono de lucide ya instalado, sin segunda librería:
  - Sustitutos: `stop` → `Square` (no existe `Stop`) y `keyframe` → `Diamond` (lucide no tiene fotograma clave; el rombo es el marcador habitual).
  - Directos: `theme-light`, `theme-dark`, `theme-system` → `Sun`, `Moon`, `Monitor`; `record` → `Circle`; `volume` → `Volume2`; `mute` → `VolumeX`; `close` → `X`; `remove` → `Trash2`; `retry` → `RotateCw`; `cancel` → `CircleX`; `open-folder` → `FolderOpen`; `star` → `Star`; `drag-handle` → `GripVertical`; `compare` → `ArrowLeftRight`; `regenerate` → `RefreshCw`; `import-file` → `FileUp`; `narration` → `AudioLines`; `queue` → `ListOrdered`; `music` → `Music`; `voices` → `Mic`; `editor` → `Film`; `scissors` → `Scissors`; `magnet` → `Magnet`; `layers` → `Layers`.
- **Descartadas**: sumar otro paquete de iconos (D-1: lucide queda fijado por klinikae). Usar `Square` para `record` en vez de `Circle`: el círculo se distingue mejor y el color de peligro lo marca como grabación.
- **Cómo revertir**: cambiar las entradas nuevas de `client/src/shared/components/atoms/UIIcon/index.tsx`.
- **Cómo comprobarla**: `bun run --cwd client vitest run UIIcon` (un caso por nombre nuevo y el de tipo, AC-1).
- **Antes de**: el merge a `dev`.
