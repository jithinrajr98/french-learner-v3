import sqlite3
from pathlib import Path
from config.settings import DB_PATH, DB_TIMEOUT
import streamlit as st


def init_db(db_path: Path):
    """
    Initialise the SQLite fallback database. Creates the `missing_words` table
    used by the vocab pages and preserves the legacy `translation_scores` table
    so historical rows aren't disturbed.
    """
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute('''
                CREATE TABLE IF NOT EXISTS missing_words (
                    word TEXT PRIMARY KEY,
                    meaning TEXT,
                    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Legacy table — no longer written to or read from in code, but kept
            # so existing rows remain intact.
            conn.execute('''
                CREATE TABLE IF NOT EXISTS translation_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sentence TEXT,
                    user_translation TEXT,
                    score INTEGER,
                    checked_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    except sqlite3.Error as e:
        raise Exception(f"Database initialization error: {e}")


def get_all_saved_words():
    try:
        with sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT) as conn:
            rows = conn.execute("SELECT word, meaning, added_on FROM missing_words ORDER BY added_on DESC").fetchall()
        return rows
    except sqlite3.Error as e:
        st.error(f"Error fetching words: {e}")
        return []


def delete_saved_word(word):
    try:
        with sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT) as conn:
            conn.execute("DELETE FROM missing_words WHERE word = ?", (word,))
            conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error deleting word: {e}")

