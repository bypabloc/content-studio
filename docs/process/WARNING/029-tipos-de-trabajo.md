# 029: studio_submit_job solo pide tipos de contenido; los de administración se rechazan

- **Contexto**: 02 §2 dice que `studio_submit_job` acepta cualquier `kind` que lista `studio_capabilities`, pero D-6 excluye
  lo administrativo. La verificación real mostró que la lista tenía `engine.install`, `engine.uninstall`,
  `storage.move`, `voice.build`, `library.scan` y `system.install_tool`: por MCP se podía desinstalar un motor.
- **Elegida**: `MCP_KINDS` en `mcp_server/tools.py`, una lista explícita de 17 tipos de contenido (narración, música,
  transcripción, limpieza, convertir, normalizar, recortar, unir, dividir, reencuadrar, subtítulos, mezcla y editor).
  `studio_submit_job` rechaza el resto con `kind_not_allowed`, y `studio_capabilities` solo lista los permitidos.
- **Descartadas**: listar todo y confiar en cada servicio (permite desinstalar motores); una regla por prefijo
  «no admin» (frágil con los tipos nuevos). El asistente (`llm.*`) queda fuera por ahora: sus sugerencias no hacen
  falta para los agentes de esta spec.
- **Cómo revertir**: ampliar `MCP_KINDS` (volvería la política abierta) y quitar la comprobación de `_submit`.
- **Cómo comprobarla**: `test_mcp_kinds_exclude_administration` y `test_submit_job_refuses_administrative_kinds`; por
  stdio, `studio_submit_job` con `engine.uninstall` responde `isError` con `kind_not_allowed`.
