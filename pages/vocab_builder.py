import streamlit as st
from core.llm_utils import LLMUtils
from core.audio import play_audio
from core.database import save_score, save_missing_words, get_all_saved_words, delete_saved_word
import sqlite3
from config.settings import DB_PATH

llm_utils = LLMUtils()

def vocab_builder():
    # Minimal CSS for compact layout
    st.markdown("""
    <style>
        .word-row {
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
            gap: 15px;
        }
        
        .word-col {
            flex: 2;
            min-width: 120px;
        }
        
        .meaning-col {
            flex: 3;
            min-width: 180px;
        }
        
        .action-col {
            flex: 1;
            min-width: 100px;
            display: flex;
            gap: 8px;
            justify-content: flex-end;
        }
        
        .word-text {
            font-weight: 600;
            color: #A7F3D0;
            margin: 0;
        }
        
        .meaning-text {
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.95rem;
            margin: 0;
        }
        .stButton>button {
            height: 38px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("### 📚 Vocabulary Builder")
    
    # Get total word count
    with sqlite3.connect(DB_PATH) as conn:
        total_words = conn.execute("SELECT COUNT(*) FROM missing_words").fetchone()[0]
    
    st.write(f"**Words saved:** {total_words}")
    st.divider()
    
    # Add new word section
    st.markdown("**➕ Add New Word**")
    add_col1, add_col2, add_col3 = st.columns([3, 1, 1])
    
    with add_col1:
        new_word = st.text_input(
            "",
            placeholder="Enter French word...",
            label_visibility="collapsed",
            key="add_word_input"
        ).strip()
    
    with add_col2:
        if st.button("Add", key="add_button", use_container_width=True):
            if len(new_word) <= 3:
                st.warning("Word must be longer than 3 characters")
            else:
                with sqlite3.connect(DB_PATH) as conn:
                    existing = conn.execute("SELECT 1 FROM missing_words WHERE word = ?", (new_word,)).fetchone()
                    if existing:
                        st.info(f"'{new_word}' already exists")
                    else:
                        with st.spinner("Getting meaning..."):
                            meaning = llm_utils.get_french_word_meaning(new_word)
                            conn.execute("INSERT INTO missing_words (word, meaning) VALUES (?, ?)", (new_word, meaning))
                            conn.commit()
                        st.success(f"Added '{new_word}'")
                        st.rerun()
    
    with add_col3:
        if st.button("🔍 Search", key="search_button", use_container_width=True):
            st.session_state.search_term = new_word
            st.rerun()
    
    st.divider()
    
    # Vocabulary list
    saved_words = get_all_saved_words()
    
    search_term = st.session_state.get('search_term', '')
    
    if search_term:
        saved_words = [
            (word, meaning, timestamp) for word, meaning, timestamp in saved_words
            if search_term.lower() in word.lower() or search_term.lower() in meaning.lower()
        ]
        if saved_words:
            st.write(f"**Found {len(saved_words)} words**")
        else:
            st.info("No words found")
            st.divider()
    
    if saved_words:
        # Header row
        header_cols = st.columns([2, 3, 0.5, 0.5])
        with header_cols[0]:
            st.markdown("<div class='word-text' style='color: white;'>Word</div>", unsafe_allow_html=True)
        with header_cols[1]:
            st.markdown("<div class='word-text' style='color: white;'>Meaning</div>", unsafe_allow_html=True)
        with header_cols[2]:
            st.markdown("<div class='word-text' style='color: white;'>🔊</div>", unsafe_allow_html=True)
        with header_cols[3]:
            st.markdown("<div class='word-text' style='color: white;'>🗑️</div>", unsafe_allow_html=True)
        st.markdown("---")

        # Word rows
        for word, meaning, timestamp in saved_words:
            row_cols = st.columns([2, 3, 0.5, 0.5])
            with row_cols[0]:
                st.markdown(f"<div class='word-text'>{word}</div>", unsafe_allow_html=True)
            with row_cols[1]:
                st.markdown(f"<div class='meaning-text'>{meaning}</div>", unsafe_allow_html=True)
            with row_cols[2]:
                if st.button("🔊", key=f"audio_{word}", help="Play pronunciation"):
                    play_audio(word)
            with row_cols[3]:
                if st.button("🗑️", key=f"delete_{word}", help="Delete"):
                    delete_saved_word(word)
                    st.rerun()
    
    else:
        if not search_term:
            st.info("No words in your vocabulary yet. Add some words above!")
            st.divider()

# Initialize session state for search
if 'search_term' not in st.session_state:
    st.session_state.search_term = ''