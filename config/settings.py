import os
from pathlib import Path


DB_TIMEOUT = 10 
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "french_learner.db"
TRANSCRIPT_EN = BASE_DIR / "data" / "english_transcript.txt"
TRANSCRIPT_FR = BASE_DIR / "data" / "french_transcript.txt"
TRANSCRIPT_YOUTUBE = BASE_DIR / "data" / "youtube_transcript.txt"

# UI Configuration
COLOR_SCHEME = {
    "primary": "#4B8BBE",
    "secondary": "#ED2939",
    "background": "#F8F9FA",
    "text": "#333333"
}

BACKGROUND = BASE_DIR / "static" / "pic_1.jpg"