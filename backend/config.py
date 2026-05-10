import os
from pathlib import Path
from typing import Literal

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates"

DATA_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

class Config:
    LLM_PROVIDER: Literal["anthropic", "dashscope", "mock"] = os.getenv("LLM_PROVIDER", "dashscope")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen-plus")

    USER_PROFILES_PATH: Path = DATA_DIR / "user_profiles.json"
    TRIP_HISTORY_PATH: Path = DATA_DIR / "trip_history.json"
    CURRENT_TRIP_PATH: Path = DATA_DIR / "current_trip.json"

    MAX_MEMORY_ITEMS: int = 100
    DEFAULT_DESTINATION: str = "日本"
    DEFAULT_SEASON: str = "春季"

config = Config()
