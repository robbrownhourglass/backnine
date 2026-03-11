from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backnine_shared.clubs import build_runtime_config


_SETTINGS = build_runtime_config("athenry", BASE_DIR)
globals().update(_SETTINGS)
