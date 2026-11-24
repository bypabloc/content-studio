"""Cliente de llama-server (spec 021, D-3): /v1/chat/completions con JSON schema, validación y un reintento.

Solo stdlib (urllib). La regla no se le confía al modelo: lo que no valida se devuelve con el error para que lo
corrija una vez; si vuelve a fallar, el trabajo termina con `llm_invalid_output`.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable

from content_studio.llm import schema as json_schema

ATTEMPTS = 2


class LlmError(RuntimeError):
    """Error del asistente con código para la cola y la API."""

    def __init__(self, code: str, problems: list[str] | None = None) -> None:
        """Conserva el código para localizarlo y, si la respuesta no cumplía, lo que falló en el último intento."""
        super().__init__(code)
        self.code = code
        self.problems = problems or []


def _post(url: str, body: dict, timeout: float) -> dict:
    request = urllib.request.Request(
        url + '/v1/chat/completions',
        data=json.dumps(body).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except TimeoutError as error:
        raise LlmError('llm_timeout') from error
    except urllib.error.URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise LlmError('llm_timeout') from error
        raise LlmError('llm_unavailable') from error


def _errors(content: str, rule: dict, check: Callable[[dict], list[str]] | None) -> tuple[dict, list[str]]:
    try:
        answer = json.loads(content)
    except ValueError as error:
        return {}, [f'$: not valid JSON ({error})']
    problems = json_schema.validate(answer, rule)
    if not problems and check is not None:
        problems = check(answer)
    return answer, problems


def chat(
    url: str,
    messages: list[dict],
    rule: dict,
    sampling: dict,
    extra: dict | None = None,
    check: Callable[[dict], list[str]] | None = None,
    timeout: float = 120.0,
    stats: dict | None = None,
) -> dict:
    """Pide una respuesta JSON que cumpla `rule` (y `check`, la validación de la tarea), con un reintento.

    `stats` recibe los tokens generados, los tok/s del último intento y cuántos intentos hicieron falta.
    """
    body = {
        'messages': list(messages),
        'response_format': {'type': 'json_schema', 'json_schema': {'name': 'answer', 'schema': rule}},
        **sampling,
        **(extra or {}),
    }
    for attempt in range(1, ATTEMPTS + 1):
        reply = _post(url, body, timeout)
        content = reply['choices'][0]['message']['content']
        if stats is not None:
            stats.update(
                completion_tokens=reply.get('usage', {}).get('completion_tokens', 0),
                tokens_per_second=reply.get('timings', {}).get('predicted_per_second', 0.0),
                attempts=attempt,
            )
        answer, problems = _errors(content, rule, check)
        if not problems:
            return answer
        body['messages'] = [
            *body['messages'],
            {'role': 'assistant', 'content': content},
            {
                'role': 'user',
                'content': 'The answer is invalid: ' + '; '.join(problems) + '. Reply again with JSON that fixes it.',
            },
        ]
    raise LlmError('llm_invalid_output', problems)
