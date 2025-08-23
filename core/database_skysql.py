import mariadb
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
from config.settings import SKYSQL_CONFIG, DB_PATH
from core.llm_utils import LLMUtils
import os
from dotenv import load_dotenv
load_dotenv()


llm_utils = LLMUtils()



# Try to get SkySQL configuration from Streamlit secrets first, then environment variables
skysql_config = {}

# Host
host = None
if hasattr(st, 'secrets') and 'SKYSQL_HOST' in st.secrets:
    host = st.secrets['SKYSQL_HOST']
elif 'SKYSQL_HOST' in os.environ:
    host = os.environ['SKYSQL_HOST']

if not host:
    raise ValueError("SKYSQL_HOST not found in Streamlit secrets or environment variables.")

# Port
port = None
if hasattr(st, 'secrets') and 'SKYSQL_PORT' in st.secrets:
    port = st.secrets['SKYSQL_PORT']
elif 'SKYSQL_PORT' in os.environ:
    port = int(os.environ['SKYSQL_PORT'])

if not port:
    raise ValueError("SKYSQL_PORT not found in Streamlit secrets or environment variables.")

# User
user = None
if hasattr(st, 'secrets') and 'SKYSQL_USER' in st.secrets:
    user = st.secrets['SKYSQL_USER']
elif 'SKYSQL_USER' in os.environ:
    user = os.environ['SKYSQL_USER']

if not user:
    raise ValueError("SKYSQL_USER not found in Streamlit secrets or environment variables.")

# Password
password = None
if hasattr(st, 'secrets') and 'SKYSQL_PASSWORD' in st.secrets:
    password = st.secrets['SKYSQL_PASSWORD']
elif 'SKYSQL_PASSWORD' in os.environ:
    password = os.environ['SKYSQL_PASSWORD']

if not password:
    raise ValueError("SKYSQL_PASSWORD not found in Streamlit secrets or environment variables.")

# Database
database = None
if hasattr(st, 'secrets') and 'SKYSQL_DATABASE' in st.secrets:
    database = st.secrets['SKYSQL_DATABASE']
elif 'SKYSQL_DATABASE' in os.environ:
    database = os.environ['SKYSQL_DATABASE']

if not database:
    raise ValueError("SKYSQL_DATABASE not found in Streamlit secrets or environment variables.")

# Create the final configuration dictionary
SKYSQL_CONFIG = {
    'host': host,
    'port': port,
    'user': user,
    'password': password,
    'database': database,
    'ssl_verify_cert': True,
    'autocommit': True
}



def get_skysql_connection():
    """Get a connection to SkySQL MariaDB"""
    try:
        conn = mariadb.connect(**SKYSQL_CONFIG)
        return conn
    except mariadb.Error as e:
        st.error(f"Error connecting to SkySQL: {e}")
        raise

def init_db():
    """Initialize the database in SkySQL"""
    try:
        # First create database if it doesn't exist
        config_without_db = SKYSQL_CONFIG.copy()
        config_without_db.pop('database', None)
        
        with mariadb.connect(**config_without_db) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS french_db")
            conn.commit()
        
        # Now create tables in the database
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            
            # Create missing_words table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS missing_words (
                    word VARCHAR(255) PRIMARY KEY,
                    meaning TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Create translation_scores table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS translation_scores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sentence TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    user_translation TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    score INT,
                    checked_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_checked_on (checked_on),
                    INDEX idx_score (score)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            conn.commit()
            
    except mariadb.Error as e:
        raise Exception(f"Database initialization error: {e}")


def save_missing_words(words: list):
    """Save missing words to SkySQL"""
    try:
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            for word in words:
                if len(word.strip()) <= 3:
                    continue
                
                # Check if word already exists - Use %s for MariaDB, not ?
                cursor.execute("SELECT 1 FROM missing_words WHERE word = %s", (word,))
                existing = cursor.fetchone()
                
                if not existing:
                    meaning = llm_utils.get_french_word_meaning(word)
                    cursor.execute(
                        "INSERT INTO missing_words (word, meaning) VALUES (%s, %s)",
                        (word, meaning)
                    )
            conn.commit()
    except mariadb.Error as e:
        st.error(f"Error saving words: {e}")

def save_score(sentence, user_translation, score):
    """Save translation score to SkySQL"""
    try:
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO translation_scores (sentence, user_translation, score) VALUES (%s, %s, %s)",
                (sentence, user_translation, score)
            )
            conn.commit()
    except mariadb.Error as e:
        st.error(f"Error saving score: {e}")

def get_all_saved_words():
    """Get all saved words from SkySQL"""
    try:
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT word, meaning, added_on FROM missing_words ORDER BY added_on DESC")
            rows = cursor.fetchall()
        return rows
    except mariadb.Error as e:
        st.error(f"Error fetching words: {e}")
        return []

def delete_saved_word(word):
    """Delete a saved word from SkySQL"""
    try:
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM missing_words WHERE word = %s", (word,))
            conn.commit()
    except mariadb.Error as e:
        st.error(f"Error deleting word: {e}")

def get_score_history():
    """Get all score history from SkySQL"""
    try:
        with get_skysql_connection() as conn:
            query = """
                SELECT 
                    id,
                    sentence,
                    user_translation,
                    score,
                    checked_on
                FROM translation_scores 
                ORDER BY checked_on ASC
            """
            df = pd.read_sql_query(query, conn)
            if not df.empty and 'score' in df.columns:
                df = df.rename(columns={'score': 'Score'})
        return df
    except mariadb.Error as e:
        st.error(f"Error fetching score history: {e}")
        return pd.DataFrame()
    
    
    
def get_word_count():
    """Get total word count from SkySQL"""
    try:
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM missing_words")
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        st.error(f"Error getting word count: {e}")
        return 0

def check_word_exists(word):
    """Check if word already exists in SkySQL"""
    try:
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM missing_words WHERE word = %s", (word,))
            return cursor.fetchone() is not None
    except Exception as e:
        st.error(f"Error checking word existence: {e}")
        return False

def add_single_word(word):
    """Add a single word to the database"""
    try:
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            corrected_word = llm_utils.correct_french_accents(word)
            meaning = llm_utils.get_french_word_meaning(corrected_word)
            cursor.execute(
                "INSERT INTO missing_words (word, meaning) VALUES (%s, %s)",
                (corrected_word, meaning)
            )
            conn.commit()
            return corrected_word, meaning
    except Exception as e:
        st.error(f"Error adding word: {e}")
        return None, None


def get_daily_scores():
    """Get average scores grouped by day from SkySQL"""
    try:
        with get_skysql_connection() as conn:
            query = """
                SELECT 
                    DATE(checked_on) as date,
                    COUNT(*) as attempt_count,
                    AVG(score) as avg_score,
                    MIN(score) as min_score,
                    MAX(score) as max_score
                FROM translation_scores 
                GROUP BY DATE(checked_on)
                ORDER BY date DESC
            """
            df = pd.read_sql_query(query, conn)
        return df
    except mariadb.Error as e:
        st.error(f"Error fetching daily scores: {e}")
        return pd.DataFrame()

def get_weekly_progress():
    """Get weekly progress data from SkySQL"""
    try:
        with get_skysql_connection() as conn:
            query = """
                SELECT 
                    YEARWEEK(checked_on, 1) as week,
                    MIN(DATE_SUB(checked_on, INTERVAL WEEKDAY(checked_on) DAY)) as week_start,
                    COUNT(*) as attempt_count,
                    AVG(score) as avg_score,
                    MIN(score) as min_score,
                    MAX(score) as max_score
                FROM translation_scores 
                GROUP BY YEARWEEK(checked_on, 1)
                ORDER BY week_start DESC
            """
            df = pd.read_sql_query(query, conn)
        return df
    except mariadb.Error as e:
        st.error(f"Error fetching weekly progress: {e}")
        return pd.DataFrame()

def get_score_statistics():
    """Get overall score statistics from SkySQL"""
    try:
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    COUNT(*) as total_attempts,
                    AVG(score) as overall_avg,
                    MIN(score) as min_score,
                    MAX(score) as max_score,
                    COUNT(DISTINCT DATE(checked_on)) as days_active
                FROM translation_scores
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                stats = {
                    'total_attempts': result[0] if result[0] else 0,
                    'overall_avg': round(float(result[1]), 2) if result[1] else 0,
                    'min_score': result[2] if result[2] else 0,
                    'max_score': result[3] if result[3] else 0,
                    'days_active': result[4] if result[4] else 0
                }
            else:
                stats = {
                    'total_attempts': 0,
                    'overall_avg': 0,
                    'min_score': 0,
                    'max_score': 0,
                    'days_active': 0
                }
        return stats
    except mariadb.Error as e:
        st.error(f"Error fetching score statistics: {e}")
        return {}

def test_connection():
    """Test the SkySQL connection"""
    try:
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return True, "Connection successful"
    except Exception as e:
        return False, f"Connection failed: {e}"

def migrate_from_sqlite():
    """Migrate data from SQLite to SkySQL"""
    import sqlite3
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(DB_PATH)
        
        # Get data from SQLite
        missing_words_data = sqlite_conn.execute(
            "SELECT word, meaning, added_on FROM missing_words"
        ).fetchall()
        
        translation_scores_data = sqlite_conn.execute(
            "SELECT sentence, user_translation, score, checked_on FROM translation_scores"
        ).fetchall()
        
        sqlite_conn.close()
        
        # Insert into SkySQL
        with get_skysql_connection() as conn:
            cursor = conn.cursor()
            
            # Migrate missing_words
            if missing_words_data:
                for word_data in missing_words_data:
                    cursor.execute(
                        "INSERT IGNORE INTO missing_words (word, meaning, added_on) VALUES (%s, %s, %s)",
                        word_data
                    )
                st.success(f"Migrated {len(missing_words_data)} words")
            
            # Migrate translation_scores
            if translation_scores_data:
                for score_data in translation_scores_data:
                    cursor.execute(
                        "INSERT INTO translation_scores (sentence, user_translation, score, checked_on) VALUES (%s, %s, %s, %s)",
                        score_data
                    )
                st.success(f"Migrated {len(translation_scores_data)} translation scores")
            
            conn.commit()
            
        st.success("Migration completed successfully!")
        
    except Exception as e:
        st.error(f"Migration error: {e}")
        raise