import sys
from pathlib import Path

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[1]

BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"

CROP_CONFIG_PATH = DATA_DIR / "crop_config.json"
READY_BUTTON_PATH = DATA_DIR / "ready_button.json"
ROUTES_DIR = DATA_DIR / "routes"
CROPPED_DIR = DATA_DIR / "cropped"