/**
 * Medidor de un nivel en dBFS (spec 010, D-2): la barra es el RMS, la marca es el pico, la banda clara es la zona objetivo
 * y la roja, el aviso de demasiado fuerte. Es un átomo porque las zonas son `div`. No tiene textos: quien lo usa pone su
 * nombre accesible.
 *
 * @since 2026/11/20
 */
type Props = {
  label: string;
  rms: number;
  peak: number;
  zone: readonly [number, number];
  alertAbove: number;
  min?: number;
  max?: number;
};

/** Posición de un nivel dentro del medidor, en porcentaje, sin salirse de él. */
function percent(db: number, min: number, max: number): number {
  return Math.min(100, Math.max(0, ((db - min) / (max - min)) * 100));
}

export function UILevelMeter({ label, rms, peak, zone, alertAbove, min = -60, max = 0 }: Props): React.JSX.Element {
  const at = (db: number) => percent(db, min, max);
  return (
    <div
      role="meter"
      aria-label={label}
      aria-valuemin={min}
      aria-valuemax={max}
      aria-valuenow={rms}
      aria-valuetext={`${rms.toFixed(1)} dBFS`} // i18n-ignore: unidad técnica del medidor, la lee el lector de pantalla
      className="relative h-3 w-full overflow-hidden rounded-full bg-muted"
    >
      <div
        className="absolute inset-y-0 bg-primary/25"
        style={{ left: `${at(zone[0])}%`, width: `${at(zone[1]) - at(zone[0])}%` }}
      />
      <div className="absolute inset-y-0 left-0 bg-primary transition-[width]" style={{ width: `${at(rms)}%` }} />
      <div className="absolute inset-y-0 right-0 bg-destructive/40" style={{ left: `${at(alertAbove)}%` }} />
      <div className="absolute inset-y-0 w-0.5 bg-foreground" style={{ left: `${at(peak)}%` }} />
    </div>
  );
}
