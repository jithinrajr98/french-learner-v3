import sqlite3
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
from config.settings import DB_PATH, DB_TIMEOUT
import streamlit as st
from core.llm_utils import LLMUtils

llm_utils = LLMUtils()



def init_db(db_path: Path):
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
    

def save_missing_words(words: list):
    try:
        with sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT) as conn:
            for word in words:
                if len(word.strip()) <= 3:
                    continue
                existing = conn.execute("SELECT 1 FROM missing_words WHERE word = ?", (word,)).fetchone()
                if not existing:
                    #correct the accents in the word
                    #word = llm_utils.correct_french_accents(word.strip())
                    #Get the meaning of the word using LLM
                    meaning = llm_utils.get_french_word_meaning(word)
                    conn.execute("INSERT INTO missing_words (word, meaning) VALUES (?, ?)", (word, meaning))
            conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error saving words: {e}")
        
        

def save_score(sentence, user_translation, score):
    try:
        with sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT) as conn:
            conn.execute(
                "INSERT INTO translation_scores (sentence, user_translation, score) VALUES (?, ?, ?)",
                (sentence, user_translation, score)
            )
            conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error saving score: {e}")
        

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
        
