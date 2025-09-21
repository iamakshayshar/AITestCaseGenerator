import configparser
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.ini"


def load_config():
    config = configparser.ConfigParser()
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    config.read(CONFIG_PATH)
    if "openai" not in config:
        raise KeyError("Config file must contain [openai] section")
    return config["openai"]
