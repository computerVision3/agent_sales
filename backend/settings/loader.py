import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "settings.yaml"

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

def get(key, default=None):
    """Helper function to safely access config keys."""
    return config.get(key, default)
