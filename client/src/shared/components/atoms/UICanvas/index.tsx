import type { ComponentProps } from 'react';

/** Canvas accesible para vistas WebGL de la aplicación. */
export function UICanvas(props: ComponentProps<'canvas'>): React.JSX.Element {
  return <canvas data-slot="canvas" {...props} />;
}
