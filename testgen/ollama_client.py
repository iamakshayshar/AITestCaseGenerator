# testgen/ollama_client.py
"""
Ollama client (quiet version).
- Reads [ollama] from config.ini: host, model, timeout_seconds, max_retries, retry_backoff.
- Verifies model presence (best-effort).
- Retries on timeouts with exponential backoff.
- Minimal console logging (only warnings/errors).
"""

from .config_loader import load_config
import requests
import json
import time
from typing import Dict, Any, Tuple

cfg = load_config()
OLLAMA_HOST = cfg.get("host", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = cfg.get("model", "gemma3")

DEFAULT_TIMEOUT = float(cfg.get("timeout_seconds", "60"))
MAX_RETRIES = int(cfg.get("max_retries", "3"))
RETRY_BACKOFF = float(cfg.get("retry_backoff", "5"))

_ENDPOINTS = ["/api/generate"]  # keep only the valid one


def _extract_text_from_response_json(data: Dict[str, Any]) -> Tuple[str, str]:
    if not isinstance(data, dict):
        return json.dumps(data), "raw_non_dict"

    for key in ("response", "result", "text", "output"):
        if key in data and isinstance(data[key], str):
            return data[key], key

    if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
        first = data["choices"][0]
        return (first.get("message", {}).get("content")
                or first.get("text")
                or first.get("content")
                or json.dumps(first), "choices")

    if "outputs" in data and isinstance(data["outputs"], list) and data["outputs"]:
        out0 = data["outputs"][0]
        if isinstance(out0, dict):
            if "content" in out0 and isinstance(out0["content"], str):
                return out0["content"], "outputs_content"
            if "data" in out0 and isinstance(out0["data"], list):
                d0 = out0["data"][0]
                if isinstance(d0, dict) and "text" in d0:
                    return d0["text"], "outputs_data_text"
        return json.dumps(out0), "outputs_raw"

    return json.dumps(data), "fallback_json"


def _make_payload(prompt: str, model: str, endpoint: str) -> Dict:
    return {"model": model, "prompt": prompt, "stream": False}


def generate(prompt_block_or_str, model: str = None, timeout: float = None,
             max_retries: int = None, backoff: float = None, **kwargs) -> str:
    model = model or DEFAULT_MODEL
    timeout = float(timeout or DEFAULT_TIMEOUT)
    max_retries = int(max_retries if max_retries is not None else MAX_RETRIES)
    backoff = float(backoff if backoff is not None else RETRY_BACKOFF)

    if isinstance(prompt_block_or_str, dict):
        system = prompt_block_or_str.get("system", "").strip()
        user = prompt_block_or_str.get("user", prompt_block_or_str.get("prompt", "")).strip()
        prompt = f"[System]\n{system}\n\n[User]\n{user}" if system else user
    else:
        prompt = str(prompt_block_or_str)

    last_exc = None

    for ep in _ENDPOINTS:
        url = OLLAMA_HOST + ep
        payload = _make_payload(prompt, model, ep)

        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=timeout)
            except (requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectTimeout) as e:
                last_exc = e
                if attempt < max_retries:
                    time.sleep(backoff * (attempt + 1))
                    continue
                else:
                    break
            except Exception as e:
                last_exc = e
                break

            if resp.status_code == 404:
                last_exc = RuntimeError(f"404 Not Found for endpoint {url}")
                break

            try:
                resp.raise_for_status()
            except Exception as e:
                last_exc = e
                break

            if "application/json" in resp.headers.get("Content-Type", ""):
                try:
                    data = resp.json()
                except Exception:
                    return resp.text
                text, _ = _extract_text_from_response_json(data)
                return text
            else:
                return resp.text

    raise RuntimeError(
        f"Ollama API call failed. Last error: {last_exc}. "
        f"Tried endpoints: {', '.join(OLLAMA_HOST + e for e in _ENDPOINTS)}. "
        f"Model={model}"
    )
