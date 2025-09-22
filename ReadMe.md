# 🧪 AI Test Case Generator

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![pytest](https://img.shields.io/badge/tests-pytest-green.svg)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![LLM](https://img.shields.io/badge/LLM-OpenAI%20%7C%20Ollama-purple.svg)](#)

A modern Python framework that auto-generates **pytest** test cases and optionally an **Excel test case sheet** from plain English requirements using **LLMs**. Supports both **OpenAI API** and **Ollama** local models, configurable via `config.ini`.

---

## ✨ Features
- 📄 **Natural language → Tests**: Write your acceptance criteria in `criteria/criterion.txt`, and let the framework generate pytest code.
- 📊 **Excel export**: Optionally generate a structured Excel file (`.xlsx`) with test case rows (`Test Name`, `Description`, `Steps`, `Expected`, etc.).
- 🔄 **Flexible LLM backend**: Choose between OpenAI (cloud) or Ollama (local) from `config.ini`.
- ⚙️ **Config-driven**: All keys, models, and provider settings live in `config.ini` (no env vars needed).
- 🛡️ **Safe defaults**: Deterministic generation (temperature=0), code-only outputs, and syntax validation.
- 🔁 **Fallbacks**: Optionally switch to a backup provider if the primary one fails.

---

## 📂 Project Structure
```
testgen-openai/
├─ criteria/              # Requirement specs in plain text
│  └─ criterion.txt        # Write your acceptance criteria here
├─ testgen/               # Core framework
│  ├─ __init__.py
│  ├─ reader.py
│  ├─ prompt.py
│  ├─ config_loader.py
│  ├─ openai_client.py
│  ├─ ollama_client.py
│  ├─ llm_router.py       # Provider selection logic
│  ├─ excel_writer.py     # Excel export module
│  └─ generator.py
├─ tests/
│  ├─ test_generated.py   # Auto-generated tests (do not edit)
│  └─ test_cases.xlsx     # Optional Excel test cases
├─ config.ini             # All settings (provider, API keys, models, export flag)
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
model = gemma3:4b

[export]
excel = true              # enable Excel export
excel_path = tests/test_cases.xlsx
```

### 3. Add Requirements
Put your acceptance criteria in `criteria/criterion.txt`, for example:
```text
1. Login: Valid credentials should sign in the user and redirect to the dashboard within 3 seconds.
2. Login: Incorrect password should display the message "Invalid email or password." without revealing which field is wrong.
3. Signup: Password must meet strength rules (≥8 chars, uppercase, lowercase, number, special character).
...
```

A longer [sample file](criteria/criterion.txt) is already included with 15 UI acceptance criteria.

### 4. Generate Tests
```bash
python run_generate.py --criterion criteria/criterion.txt
```

Generated artifacts:
- ✅ `tests/test_generated.py` (pytest tests)
- 📊 `tests/test_cases.xlsx` (Excel test sheet, if enabled)

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
- 📊 Excel export uses `openpyxl` — lightweight and configurable.
- 🔒 API keys are never hard-coded — only read from `config.ini`.

---

## 📜 License
MIT — free to use, modify, and share.

---

## 🙌 Acknowledgements
- [OpenAI](https://platform.openai.com/) for API access.
- [Ollama](https://ollama.ai) for local LLMs.
- [pytest](https://pytest.org) for a clean testing experience.
- [openpyxl](https://openpyxl.readthedocs.io/) for Excel generation.

---

> 🚧 **Tip:** Review generated tests before committing them to production. LLMs may make assumptions about imports or edge cases.