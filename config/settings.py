import os
from pathlib import Path


DB_TIMEOUT = 10
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "french_learner.db"

# UI Configuration
COLOR_SCHEME = {
    "primary": "#4B8BBE",
    "secondary": "#ED2939",
    "background": "#F8F9FA",
    "text": "#333333"
}

BACKGROUND = BASE_DIR / "static" / "pic_10.jpg"  #pic_7.jpg

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_EVAL_MODEL = "llama-3.3-70b-versatile"
GROQ_SCORE_MODEL = "llama-3.3-70b-versatile"

