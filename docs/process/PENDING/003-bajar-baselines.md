# 003: vaciar los baselines a medida que se tocan los archivos

- **Qué**: `tests/validators/file-size.baseline.json` (9 instrucciones), `mirror.baseline.json` (41 módulos sin test espejo), `coverage.baseline.json` (18 archivos bajo el 80 %) y la lista de overrides de mypy en `pyproject.toml` (23 módulos). `cli/` salió del alcance de cobertura y de mypy en la 004, al reescribirse; `grabar/` sale en la 007.
- **Por qué no se hizo**: la 003 hace cumplir las reglas y deja registrada la deuda; cubrir 41 módulos y corregir 79 errores de tipos es trabajo de producto, fuera de alcance del runner (la spec dice «se cubren a medida que se tocan»).
- **Cuándo**: en cada spec que toque un módulo de la lista: la entrada sale del baseline en el mismo PR que añade su test o corrige su tipo. La 008 reescribe `grabar/`.
- **Quién**: agente, en la spec que toca cada módulo.
- **Qué la cierra**: `python -m devtools test-runner --type=all --git-mode=all` pasa con los baselines vacíos de los módulos tocados, y la lista de overrides de mypy no contiene ningún módulo ya corregido.
