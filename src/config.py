from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"
CROP_CONFIG_PATH = DATA_DIR / "crop_config.json"

CROPPED_DIR = DATA_DIR / "cropped"
ROUTES_DIR = DATA_DIR / "routes"

MONITOR_INDEX = 1

# If the best score is below this, the script will refuse to run a route.
SPAWN_CONFIDENCE_THRESHOLD = 0.60

# After route playback, press F6 if the route file does not already contain F6.
PRESS_F6_AFTER_ROUTE_IF_MISSING = True