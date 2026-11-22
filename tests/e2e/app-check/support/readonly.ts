import type { Page } from '@playwright/test';

/** La API local de la app: 127.0.0.1 con el puerto que eligió el server. */
const LOCAL_API = /^http:\/\/127\.0\.0\.1:\d+\//;

/**
 * Solo lectura (spec 024, D-4): aborta toda petición a la API que no sea GET y la anota. Con `--data=real` la app ve
 * los datos del usuario, y así ningún escenario los cambia aunque lo intente.
 */
export async function readOnlyApi(page: Page, api: RegExp = LOCAL_API): Promise<string[]> {
  const blocked: string[] = [];
  await page.route(api, async (route) => {
    const request = route.request();
    if (request.method() === 'GET') return route.fallback();
    blocked.push(`${request.method()} ${new URL(request.url()).pathname}`);
    return route.abort('blockedbyclient');
  });
  return blocked;
}
