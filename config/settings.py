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

# openai/gpt-oss-120b is Groq's strongest production model (checked Nov 2026);
# llama-3.3-70b-versatile is no longer available to this account.
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_EVAL_MODEL = "openai/gpt-oss-120b"
GROQ_SCORE_MODEL = "openai/gpt-oss-120b"
# gpt-oss is a reasoning model; "low" keeps short tasks fast (~0.5s).
GROQ_REASONING_EFFORT = "low"

