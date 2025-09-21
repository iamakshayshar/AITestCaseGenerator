# testgen/ollama_client.py
"""
Simple wrapper for Ollama REST API to generate text.
"""

import json

import requests

from .config_loader import load_config

cfg = load_config()
OLLAMA_HOST = cfg.get("host", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = cfg.get("model", "gemma3")


def generate(prompt_block_or_str, model: str = DEFAULT_MODEL, **kwargs) -> str:
    """
    Generate output using Ollama REST API.
    Accepts either a dict {'system':..., 'user':...} or a plain string prompt.
    """
    if isinstance(prompt_block_or_str, dict):
        system = prompt_block_or_str.get("system", "")
        user = prompt_block_or_str.get("user", "")
        prompt = f"[System]\\n{system}\\n\\n[User]\\n{user}".strip()
    else:
        prompt = str(prompt_block_or_str)

    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Ollama API call failed: {e}")

    data = resp.json()
    # depending on version, output may be in different fields
    if "response" in data:
        return data["response"]
    if "result" in data:
        return data["result"]
    if "choices" in data:
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            return json.dumps(data)
    return json.dumps(data)
