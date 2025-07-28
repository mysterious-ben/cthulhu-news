import json

import litellm
from loguru import logger


# @retry(stop=stop_after_attempt(2), wait=wait_fixed(1.0))
def get_llm_json_response(
    gpt_role: str,
    gpt_query: str,
    gpt_model: str,
    gpt_max_tokens: int,
) -> dict:
    gpt_messages = [
        {"role": "system", "content": gpt_role},
        {"role": "user", "content": gpt_query},
    ]
    logger.debug(f"prompt_length={len(gpt_query)} model={gpt_model} max_tokens={gpt_max_tokens}")
    response = litellm.completion(
        model=gpt_model,  # Can be "gpt-4", "claude-3-opus", "gemini-pro", etc.
        messages=gpt_messages,  # type: ignore
        stream=False,
        max_tokens=gpt_max_tokens,
        n=1,
        stop=None,
        frequency_penalty=0,
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    response_json = json.loads(response.choices[0].message.content)  # type: ignore
    return response_json
