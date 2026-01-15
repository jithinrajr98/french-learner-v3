# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Create virtual environment and install dependencies (using uv)
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The app runs on `http://localhost:8501`

## Environment Variables

Required in `.env`:
```
GROQ_API_KEY=<your-groq-api-key>
SUPABASE_URL=<supabase-project-url>       # optional, falls back to SQLite
SUPABASE_API_KEY=<supabase-anon-key>      # optional
```

## Architecture

This is a Streamlit app for French language learning with AI-powered translation evaluation.

### Core Flow
1. `app.py` - Entry point, initializes databases and routes to page modules
2. User practices translations on the Writing Practice page
3. `core/evaluation.py` evaluates translations and scores them (0-10)
4. `core/llm_utils.py` handles all Groq LLM calls
5. Missed vocabulary words are saved with meanings to the database

### Key Modules

**config/**
- `settings.py` - Paths, model names, constants. Models: `GROQ_MODEL`, `GROQ_EVAL_MODEL`, `GROQ_SCORE_MODEL`, `GROQ_TRANSCRIPT_MODEL`
- `styles.py` - Streamlit CSS, header, sidebar navigation

**core/**
- `llm_utils.py` - `LLMUtils` class wrapping Groq API: word meanings, accent correction, missed word extraction, example sentences, verb conjugations, YouTube transcript processing
- `evaluation.py` - `check_translation()` for feedback, `scorer()` for 0-10 scoring
- `database.py` - SQLite operations (local fallback)
- `database_supabase.py` - Supabase cloud database operations
- `transcript_processing.py` - `TranscriptManager` for loading/randomizing sentence pairs
- `audio.py` - gTTS audio playback

**page_modules/**
- `writing_practise.py` - Main translation practice page
- `vocab_builder.py` - View/delete saved vocabulary
- `vocab_practise.py` - Flash card practice with audio
- `transcript_viewer.py` - YouTube transcript extraction and processing
- `performance_analyser.py` - Progress analytics with Altair charts

### Database Schema

Two tables (SQLite and Supabase):
- `missing_words`: word (PK), meaning, added_on
- `translation_scores`: id, sentence, user_translation, score, checked_on

### Data Files

- `data/english_transcript.txt` - English sentences (one per line)
- `data/french_transcript.txt` - Corresponding French translations (same line numbers)
- `data/youtube_transcript.txt` - Extracted YouTube transcript
- `data/french_learner.db` - SQLite database

### State Management

Uses `st.session_state` extensively:
- `db_status`: "supabase" | "local" | "error"
- Sentence randomization state in `TranscriptManager`
