import streamlit as st
from core.database_skysql import get_all_saved_words, delete_saved_word
import random
from core.audio import play_audio_mobile_compatible
from core.llm_utils import LLMUtils

llm_utils = LLMUtils()

def vocab_practise():
    
    
    st.markdown("""
    <style>
        .english-text {
            font-size: 1.3rem;
            font-weight: 500;
            color: white;
            margin: 1rem 0;
            padding: 1.5rem;
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            text-align: center;
            border-left: 4px solid #10B981;

        }
        .score-badge {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 1rem;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    
    # Set a minimalistic page title
    st.divider()
    st.markdown("#### 🎯 Vocabulary Workout")
    st.caption("Practice your vocabulary with saved words. Click 'New Word' to get started or 'Delete Word' to remove a word from your list.")
    # Initialize session state
    if 'word_index' not in st.session_state:
        st.session_state.word_index = 0

    saved_words = get_all_saved_words()

    if not saved_words:
        st.info("📚 No words available. Add some words to your vocabulary first!")
        return

    # Handle case where word index might be out of bounds
    if st.session_state.word_index >= len(saved_words):
        st.session_state.word_index = 0

    # Get current word
    current_word, current_meaning = saved_words[st.session_state.word_index][:2]
    
    # Main word display
    st.markdown(f'<div class="english-text"> {current_word}</div>', unsafe_allow_html=True)

    # Action buttons (New Word and Delete) in a single row
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Word", use_container_width=True):
            st.session_state.word_index = random.randint(0, len(saved_words) - 1)
            st.rerun()

    with col2:
        if st.button("🗑️ Delete Word", use_container_width=True):
            delete_saved_word(current_word)  
            st.success(f"Deleted word: `{current_word}`")
            if len(saved_words) > 1:
                st.session_state.word_index = random.randint(0, len(saved_words) - 2)
            else:
                st.session_state.word_index = 0
            st.rerun()
    
    st.markdown("---")

    # Meaning section
    st.markdown("#### 📖 Meaning")
    st.success(current_meaning)
    
    # Example sentence section
    if 'example_sentence' not in st.session_state or st.session_state.get('current_practice_word') != current_word:
            st.session_state.example_sentence = llm_utils.example_sentence_generator(current_word)
            st.session_state.current_practice_word = current_word
            
    if hasattr(st.session_state, 'example_sentence'):
        st.markdown("#### 💡 Example Sentence")
        st.info(st.session_state.example_sentence)
    
    # Audio section
    st.markdown("#### 🎵 Pronounciation")
    audio_col1, audio_col2 = st.columns(2)
    with audio_col1:
        if st.button("🔊 Listen word",use_container_width=True):
            play_audio_mobile_compatible(st.session_state.current_practice_word)
    
    with audio_col2:
        # Generate example sentence using LLM
        if st.button("🔊 Listen sentence",  use_container_width=True):
            play_audio_mobile_compatible(st.session_state.example_sentence,)
    
    # Conjugation details (if it's a verb)
    conjugation_info = llm_utils.conjugation_details(current_word)
    if conjugation_info and "not a verb" not in conjugation_info.lower():
        st.markdown("### 🔄 Conjugation")
        st.info(conjugation_info)

    st.markdown("---")
  
    
    # Progress indicator
    st.markdown(f"**Progress:** Word {st.session_state.word_index + 1} of {len(saved_words)} | Total words: {len(saved_words)}")