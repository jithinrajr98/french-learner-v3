import os
from pathlib import Path


DB_TIMEOUT = 10 
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "french_learner.db"
TRANSCRIPT_EN = BASE_DIR / "data" / "english_transcript.txt"
TRANSCRIPT_FR = BASE_DIR / "data" / "french_transcript.txt"
TRANSCRIPT_YOUTUBE = BASE_DIR / "data" / "youtube_transcript.txt"
LINK_YOUTUBE = BASE_DIR / "data" / "youtube_link.txt"

# UI Configuration
COLOR_SCHEME = {
    "primary": "#4B8BBE",
    "secondary": "#ED2939",
    "background": "#F8F9FA",
    "text": "#333333"
}

BACKGROUND = BASE_DIR / "static" / "pic_10.jpg"  #pic_7.jpg

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TRANSCRIPT_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
VOSK_MODEL_PATH = BASE_DIR / "models" / "vosk-model-small-fr-0.22/" 

