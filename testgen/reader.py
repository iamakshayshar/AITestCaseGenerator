from pathlib import Path


def read_criterion(path: str) -> str:
    """Read and return the text content of the criterion file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Criterion file not found: {path}")
    return p.read_text(encoding="utf-8").strip()
