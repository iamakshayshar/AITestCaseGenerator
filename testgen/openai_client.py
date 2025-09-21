from typing import Dict

import openai

from .config_loader import load_config

cfg = load_config()
API_KEY = cfg.get("api_key")
DEFAULT_MODEL = cfg.get("model", "gpt-3.5-turbo")

if not API_KEY:
    raise RuntimeError("Missing 'api_key' in config.ini under [openai] section")

# Create a client instance (new API style)
client = openai.OpenAI(api_key=API_KEY)


def _messages_from_prompt_block(prompt_block: Dict[str, str]) -> list:
    messages = []
    if "system" in prompt_block:
        messages.append({"role": "system", "content": prompt_block["system"]})
    if "user" in prompt_block:
        messages.append({"role": "user", "content": prompt_block["user"]})
    return messages


def generate(prompt_block: Dict[str, str],
             model: str = DEFAULT_MODEL,
             temperature: float = 0.0,
             max_tokens: int = 1500) -> str:
    messages = _messages_from_prompt_block(prompt_block)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {e}") from e

    return resp.choices[0].message.content
