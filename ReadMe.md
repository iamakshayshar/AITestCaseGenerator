# 🧪 AI Test Case Generator

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![pytest](https://img.shields.io/badge/tests-pytest-green.svg)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![LLM](https://img.shields.io/badge/LLM-OpenAI%20%7C%20Ollama-purple.svg)](#)

A modern Python framework that auto-generates **pytest** test cases from plain English requirements using **LLMs**. Supports both **OpenAI API** and **Ollama** local models, configurable via `config.ini`.

---

## ✨ Features
- 📄 **Natural language → Tests**: Write your acceptance criteria in `criteria/criterion.txt`, and let the framework generate pytest code.
- 🔄 **Flexible LLM backend**: Choose between OpenAI (cloud) or Ollama (local) from `config.ini`.
- ⚙️ **Config-driven**: All keys, models, and provider settings live in `config.ini` (no env vars needed).
- 🛡️ **Safe defaults**: Deterministic generation (temperature=0), code-only outputs, and syntax validation.
- 🔁 **Fallbacks**: Optionally switch to a backup provider if the primary one fails.

---

## 📂 Project Structure
```
testgen-openai/
├─ criteria/              # Requirement specs in plain text
│  └─ criterion.txt
├─ testgen/               # Core framework
│  ├─ __init__.py
│  ├─ reader.py
│  ├─ prompt.py
│  ├─ config_loader.py
│  ├─ openai_client.py
│  ├─ ollama_client.py
│  ├─ llm_router.py       # Provider selection logic
│  └─ generator.py
├─ tests/
│  └─ test_generated.py   # Auto-generated tests (do not edit)
├─ config.ini             # All settings (provider, API keys, models)
├─ requirements.txt
└─ run_generate.py        # CLI entrypoint
```

---

## 🚀 Quickstart

### 1. Clone & Setup
```bash
git clone <your-repo-url> aitestgen
cd aitestgen
python -m venv .venv
source .venv/bin/activate   # mac/linux
.\.venv\Scripts\activate    # windows
pip install -r requirements.txt
```

### 2. Configure
Edit `config.ini`:
```ini
[llm]
provider = openai         # or ollama
fallback_enabled = true
fallback_provider = ollama

[openai]
api_key = sk-...
model = gpt-3.5-turbo

[ollama]
host = http://localhost:11434
model = gemma3
```

### 3. Add Requirements
Put your spec in `criteria/criterion.txt`:
```text
The function `is_prime(n)` must:
- Return True for prime numbers.
- Return False for composites.
- Raise ValueError for invalid input.
```

### 4. Generate Tests
```bash
python run_generate.py --criterion criteria/criterion.txt
```

Generated tests appear in `tests/test_generated.py`.

### 5. Run Tests
```bash
pytest -q
```

---

## ⚡ Switching Providers
- To use **OpenAI**: set `[llm] provider=openai` and fill `[openai] api_key`.
- To use **Ollama**: set `[llm] provider=ollama` and ensure Ollama server is running (`ollama serve`).
- You can enable automatic fallback in `config.ini`.

---

## 🛠️ Developer Notes
- 🧩 **Prompt design** lives in `testgen/prompt.py` — tweak it to change generation style.
- ✅ Generated code is syntax-checked before writing.
- 🧪 Supports `pytest.raises` for exceptions.
- 🔒 API keys are never hard-coded — only read from `config.ini`.

---

## 📜 License
MIT — free to use, modify, and share.

---

## 🙌 Acknowledgements
- [OpenAI](https://platform.openai.com/) for API access.
- [Ollama](https://ollama.ai) for local LLMs.
- [pytest](https://pytest.org) for a clean testing experience.

---

> 🚧 **Tip:** Review generated tests before committing them to production. LLMs may make assumptions about imports or edge cases.