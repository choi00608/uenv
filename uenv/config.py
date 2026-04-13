import os
from pathlib import Path

# ~/.uenv 
GLOBAL_UENV_DIR = Path.home() / ".uenv"
GLOBAL_ENVS_DIR = GLOBAL_UENV_DIR / "envs"

def ensure_global_dir():
    if not GLOBAL_ENVS_DIR.exists():
        GLOBAL_ENVS_DIR.mkdir(parents=True, exist_ok=True)
