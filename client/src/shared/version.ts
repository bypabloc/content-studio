import packageJson from '../../package.json';

// La versión la escribe `python -m devtools version` en package.json (spec 022, D-7): aquí no se repite.
export const APP_VERSION = packageJson.version;
