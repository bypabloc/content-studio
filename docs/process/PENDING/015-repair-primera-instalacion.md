# Instalador: `repair` rechaza un motor cuya primera instalación no terminó

**Qué queda.** `installer.install(recipe, root, repair=True)` lanza `engine_external` si el motor no tiene `install.json`, es decir, si su primera instalación nunca terminó. El job de `studio engines repair <motor>` falla en 0 % sin mensaje útil, y desde la app no hay salida: reinstalar pide `repair`.

**Cómo se vio.** Con el motor `vision`, la primera instalación falló en el paso `hf` (faltaba `huggingface-hub`). `studio engines repair vision` falló al 0 %. Llamar a `installer.install(..., repair=True)` directo dio `InstallError: engine_external` en `installer.py`, línea 131.

**Por qué no se tocó aquí.** Es del instalador de motores (spec 009), fuera del alcance de 015. Se resolvió subiendo la `version` de la receta, que fuerza los pasos sin borrar nada.

**Qué hacer.** Permitir `repair` cuando hay `installing.json` (una instalación pendiente o fallida), o que la app ofrezca reinstalar en ese caso. Empezar con un test RED en `server/tests/unit/src/content_studio/engines/test_installer.py`.
