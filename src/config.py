from pathlib import Path
import sys

def get_base_dir():
    # When running as .exe
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    # When running from Python / VS Code
    return Path(__file__).resolve().parents[1]


ROOT_DIR = get_base_dir()

DATA_DIR = ROOT_DIR / "data"
CROP_CONFIG_PATH = DATA_DIR / "crop_config.json"

CROPPED_DIR = DATA_DIR / "cropped"
ROUTES_DIR = DATA_DIR / "routes"
READY_BUTTON_PATH = DATA_DIR / "ready_button.json"

MONITOR_INDEX = 1

# If the best score is below this, the script will refuse to run a route.
SPAWN_CONFIDENCE_THRESHOLD = 0.0

# After route playback, press F6 if the route file does not already contain F6.
PRESS_F6_AFTER_ROUTE_IF_MISSING = True