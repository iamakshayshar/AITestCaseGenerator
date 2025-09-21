# testgen/llm_router.py
"""
LLM router: choose between OpenAI and Ollama based on config.ini.

Behaviour:
- Reads config.ini from the project root (same location other modules expect).
- Uses provider from [llm] -> provider (openai | ollama). Defaults to 'openai'.
- If fallback_enabled=true and primary fails, it will try fallback_provider.
- Calls underlying client.generate(...) and adapts prompt format if necessary.
- You can override provider per-call by passing _provider="ollama" (as a kwarg).
"""

import configparser
from pathlib import Path
from typing import Dict, Optional, Callable

# ---- load config.ini ----
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.ini"

_config = configparser.ConfigParser()
if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"config.ini not found at expected path: {CONFIG_PATH}")
_config.read(CONFIG_PATH)

_llm_section = _config["llm"] if "llm" in _config else {}
DEFAULT_PROVIDER = _llm_section.get("provider", "openai").strip().lower()
FALLBACK_ENABLED = _llm_section.get("fallback_enabled", "false").strip().lower() in ("1", "true", "yes")
FALLBACK_PROVIDER = _llm_section.get("fallback_provider", "").strip().lower()


# ---- lazy client import helpers ----
def _import_openai_client() -> Callable[..., str]:
    try:
        # openai_client.generate(prompt_block: Dict, model=None, **kwargs) -> str
        from .openai_client import generate as openai_generate
        return openai_generate
    except Exception as e:
        raise RuntimeError(f"OpenAI client import failed: {e}") from e


def _import_ollama_client() -> Callable[..., str]:
    try:
        # ollama_client.generate(prompt: str or prompt_block, model=..., **kwargs) -> str
        from .ollama_client import generate as ollama_generate
        return ollama_generate
    except Exception as e:
        raise RuntimeError(f"Ollama client import failed: {e}") from e


_CLIENT_FACTORY = {
    "openai": _import_openai_client,
    "ollama": _import_ollama_client,
}


# ---- prompt normalization helpers ----
def _prompt_block_to_text(prompt_block: Dict[str, str]) -> str:
    """Convert a prompt_block {'system':..., 'user':...} into a single string fallback for clients that expect plain text."""
    parts = []
    sys_msg = prompt_block.get("system")
    user_msg = prompt_block.get("user") or prompt_block.get("prompt") or ""
    if sys_msg:
        parts.append(f"[System]\n{sys_msg.strip()}\n")
    if user_msg:
        parts.append(f"[User]\n{user_msg.strip()}")
    return "\n\n".join(parts).strip()


def _call_client_adaptive(client_callable: Callable[..., str], prompt_block: Dict[str, str], model: Optional[str],
                          **kwargs) -> str:
    """
    Try calling client with prompt_block dict first (preferred).
    If that raises a TypeError (signature mismatch) or other evidence the client expects a plain string,
    call it with the combined string fallback.
    """
    # 1) Try preferred signature
    try:
        if model is not None:
            return client_callable(prompt_block, model=model, **kwargs)
        else:
            return client_callable(prompt_block, **kwargs)
    except TypeError:
        # signature mismatch: maybe the client expects a plain string prompt
        text_prompt = _prompt_block_to_text(prompt_block)
        if model is not None:
            return client_callable(text_prompt, model=model, **kwargs)
        else:
            return client_callable(text_prompt, **kwargs)
    except Exception:
        # For other exceptions, re-raise to allow router fallback logic to run
        raise


# ---- main router function ----
def generate(prompt_block: Dict[str, str], model: Optional[str] = None, **kwargs) -> str:
    """
    Generate text using the configured provider.
    - prompt_block: dict with keys 'system' and 'user' (as produced by build_prompt).
    - model: optional model override for the underlying client.
    - kwargs: passed to underlying client (temperature, max_tokens). Special: pass _provider to override provider.
    """
    # Allow call-time override of provider
    provider = kwargs.pop("_provider", None)
    provider = (provider or DEFAULT_PROVIDER).strip().lower()

    def _resolve_and_call(p: str):
        if p not in _CLIENT_FACTORY:
            raise ValueError(f"Unknown LLM provider '{p}'. Supported: {list(_CLIENT_FACTORY.keys())}")
        client_factory = _CLIENT_FACTORY[p]
        client = client_factory()  # may raise RuntimeError if import fails
        return _call_client_adaptive(client, prompt_block, model, **kwargs)

    # Try primary provider
    try:
        return _resolve_and_call(provider)
    except Exception as primary_exc:
        # If fallback is enabled, try fallback provider
        if FALLBACK_ENABLED and FALLBACK_PROVIDER:
            fb = FALLBACK_PROVIDER
            # Avoid fallback to same provider
            if fb == provider:
                raise RuntimeError(
                    f"Primary provider '{provider}' failed and fallback_provider is identical.") from primary_exc
            try:
                print(f"[llm_router] primary provider '{provider}' failed: {primary_exc}. Trying fallback '{fb}'")
                return _resolve_and_call(fb)
            except Exception as fallback_exc:
                raise RuntimeError(
                    f"Both primary provider '{provider}' and fallback '{fb}' failed. "
                    f"Primary error: {primary_exc}; Fallback error: {fallback_exc}"
                ) from fallback_exc
        # No fallback or fallback failed: raise informative error
        raise RuntimeError(f"LLM generation failed for provider '{provider}': {primary_exc}") from primary_exc
