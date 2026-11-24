export type Lut3D = {
  size: number;
  data: Uint8Array;
  domainMin: [number, number, number];
  domainMax: [number, number, number];
};

/** Lee una LUT 3D `.cube`, donde rojo cambia más rápido, en el orden de una textura WebGL. */
export function parseCube(source: string): Lut3D {
  let size = 0;
  let domainMin: [number, number, number] = [0, 0, 0];
  let domainMax: [number, number, number] = [1, 1, 1];
  const rows: Array<[number, number, number]> = [];
  for (const raw of source.split(/\r?\n/)) {
    const line = raw.split('#', 1)[0].trim();
    if (!line) continue;
    const parts = line.split(/\s+/);
    if (parts[0] === 'TITLE') continue;
    if (parts[0] === 'LUT_3D_SIZE' && parts.length === 2 && !size) {
      size = Number(parts[1]);
      if (!Number.isInteger(size) || size < 2 || size > 64) throw new Error('Invalid 3D LUT');
      continue;
    }
    if ((parts[0] === 'DOMAIN_MIN' || parts[0] === 'DOMAIN_MAX') && parts.length === 4) {
      const domain = parts.slice(1).map(Number);
      if (!domain.every(Number.isFinite)) throw new Error('Invalid 3D LUT');
      if (parts[0] === 'DOMAIN_MIN') domainMin = domain as [number, number, number];
      else domainMax = domain as [number, number, number];
      continue;
    }
    const values = parts.map(Number);
    if (parts.length !== 3 || !values.every((value) => Number.isFinite(value) && value >= 0 && value <= 1)) {
      throw new Error('Invalid 3D LUT');
    }
    rows.push(values as [number, number, number]);
    if (rows.length > size ** 3) throw new Error('Invalid 3D LUT');
  }
  if (!size || rows.length !== size ** 3 || domainMin.some((value, index) => value >= domainMax[index])) {
    throw new Error('Invalid 3D LUT');
  }
  const data = new Uint8Array(rows.length * 3);
  for (let red = 0; red < size; red++) {
    for (let green = 0; green < size; green++) {
      for (let blue = 0; blue < size; blue++) {
        const sourceIndex = (blue * size * size + green * size + red) * 3;
        const targetIndex = sourceIndex;
        for (let channel = 0; channel < 3; channel++) {
          data[targetIndex + channel] = Math.round(rows[sourceIndex / 3][channel] * 255);
        }
      }
    }
  }
  return { size, data, domainMin, domainMax };
}
