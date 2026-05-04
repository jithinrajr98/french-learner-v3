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

**Local development** - use `.env`:
```
GROQ_API_KEY=<your-groq-api-key>
SUPABASE_URL=<supabase-project-url>       # optional, falls back to SQLite
SUPABASE_API_KEY=<supabase-anon-key>      # optional
```

**Streamlit Cloud** - use secrets dashboard (TOML format):
```toml
GROQ_API_KEY = "your-key"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_API_KEY = "your-key"
```

See `.streamlit/secrets.toml.example` for template. Code uses `st.secrets` with fallback to `os.getenv()`.

## Architecture

This is a Streamlit app for French language learning, built around a personal vocabulary list and AI-powered spaced-repetition practice.

### Core Flow
1. `app.py` - Entry point, initializes databases and routes to page modules
2. The Memorise page drives study (review cards, story mode, writing practice)
3. `core/llm_utils.py` handles all Groq LLM calls (grading, story/exercise generation, word meanings)
4. `core/evaluation.py` provides translation feedback and 0-10 scoring used by Memorise's writing mode
5. Vocabulary CRUD lives in the Explore Vocabulary and Practise Vocabulary pages

### Key Modules

**config/**
- `settings.py` - Paths, model names, constants. Models: `GROQ_MODEL`, `GROQ_EVAL_MODEL`, `GROQ_SCORE_MODEL`
- `styles.py` - Streamlit CSS, header, sidebar navigation

**core/**
- `llm_utils.py` - `LLMUtils` class wrapping Groq API: word meanings, accent correction, example sentences, flashcard grading, story generation, writing exercise generation
- `evaluation.py` - `check_translation()` for feedback, `scorer()` for 0-10 scoring (used by Memorise's Write mode)
- `database.py` - SQLite operations (local fallback): `init_db`, `get_all_saved_words`, `delete_saved_word`
- `database_supabase.py` - Supabase cloud database operations: vocab CRUD plus spaced-repetition helpers (`get_due_words`, `update_review`, `get_recently_reviewed`, `count_due_today`)
- `audio.py` - gTTS audio playback (`play_audio_mobile_compatible`)

**page_modules/**
- `vocab_builder.py` - Add/search/delete saved vocabulary
- `vocab_practise.py` - Flash card practice with audio
- `memorise.py` - Spaced-repetition Review, AI-generated Write, and Story modes (default page)

### Database Schema

Tables (SQLite and Supabase):
- `missing_words`: word (PK), meaning, added_on
- `vocab_reviews`: word (PK), interval_days, next_due, correct_count, wrong_count, last_reviewed (Supabase only — see `data/vocab_reviews_migration.sql`)
- `translation_scores`: id, sentence, user_translation, score, checked_on — **legacy**, no longer read or written by code, retained so historical rows survive

### Data Files

- `data/french_learner.db` - SQLite database
- `data/vocab_reviews_migration.sql` - Supabase migration for the spaced-repetition table

### State Management

Uses `st.session_state` extensively:
- `db_status`: "supabase" | "local" | "error"
- Memorise session: `mem_cards`, `mem_index`, `mem_result`, `mem_correct`, `mem_wrong`, `mem_write_exercise`, `mem_write_result`, `mem_last_story`
