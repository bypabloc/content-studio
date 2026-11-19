# 006: la licencia se guarda por motor y la elección espera a que se guarde

- **Contexto**: AC-7 pide que aceptar guarde `license.accepted.<motor>` y que no vuelva a preguntar, y que cancelar deje el selector en la opción anterior. Las decisiones de la 006 hablan de una «confirmación única guardada en settings».
- **Elegida**: un ajuste por motor (`narration.license.accepted.<motor>`), que es lo que AC-7 nombra. Se lee con la caché de react-query (`ensureQueryData`): tras aceptar, la caché manda aunque la API responda otra cosa. Si la API no responde, se vuelve a preguntar. Aceptar espera al PUT: si falla, la elección no se aplica y el aviso se cierra igual. `RecommendedSelect` recibe `beforeChange`: la elección solo se aplica si esa función responde que sí.
- **Descartadas**: una sola confirmación para todos los motores no comerciales (AC-7 pide la clave por motor); guardar solo en estado del componente (se perdería al recargar y AC-7 exige guardarla); `fetchQuery` (con `staleTime` 0 vuelve a pedir el ajuste y reabre el aviso aunque ya se aceptó; la prueba de AC-7 lo detectó).
- **Cómo revertir**: quitar `beforeChange` del selector de motor en `NarrationOptions.tsx`; el ajuste guardado queda sin uso.
- **Cómo comprobarla**: `client/tests/unit/src/features/narration/NarrationOptions.test.tsx` (AC-7: cancelar y aceptar) y `client/tests/unit/src/shared/components/LicenseDialog.test.tsx`.
- **Antes de**: el merge a `dev`.
