import streamlit as st
from core.database_supabase import SupabaseDB
import random
import html
from core.audio import play_audio_mobile_compatible
from core.llm_utils import LLMUtils

llm_utils = LLMUtils()
supabase_client = SupabaseDB()

def vocab_practise():

    st.markdown("""
    <style>
        .vocab-card {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            max-width: 600px;
            margin: 1rem auto;
        }
        .word-section {
            text-align: center;
            padding-bottom: 1.5rem;
        }
        .word-text {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1a1a2e !important;
            display: block;
        }
        .meaning-text {
            font-size: 1.1rem;
            color: #555 !important;
            margin-top: 0.5rem;
            display: block;
        }
        .example-section {
            border-top: 1px solid #e0e0e0;
            padding-top: 1.5rem;
            margin-top: 0.5rem;
        }
        .example-label {
            font-size: 1rem;
            color: #888 !important;
            margin-bottom: 0.8rem;
            display: block;
        }
        .example-text {
            font-size: 1.1rem;
            font-style: italic;
            color: #333 !important;
            display: block;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'word_index' not in st.session_state:
        st.session_state.word_index = 0

    # Get saved words from Supabase
    try:
        saved_words_data = supabase_client.get_all_saved_words()
        saved_words = [(item['word'], item['meaning'], item.get('added_on', '')) for item in saved_words_data]
    except Exception as e:
        st.error(f"Error fetching vocabulary: {e}")
        saved_words = []

    if not saved_words:
        st.info("No words available. Add some words to your vocabulary first!")
        return

    # Handle bounds
    if st.session_state.word_index >= len(saved_words):
        st.session_state.word_index = 0
    if st.session_state.word_index < 0:
        st.session_state.word_index = len(saved_words) - 1

    # Get current word
    word_data = saved_words[st.session_state.word_index]
    current_word = word_data[0] if word_data[0] else "Unknown"
    current_meaning = word_data[1] if len(word_data) > 1 and word_data[1] else "No meaning available"

    # HTML escape to prevent breaking the card
    current_word_display = html.escape(str(current_word))
    current_meaning_display = html.escape(str(current_meaning))

    # Generate example sentence
    if 'example_sentence' not in st.session_state or st.session_state.get('current_practice_word') != current_word:
        try:
            st.session_state.example_sentence = llm_utils.example_sentence_generator(current_word)
        except Exception as e:
            st.session_state.example_sentence = "Could not generate example"
        st.session_state.current_practice_word = current_word

    example_sentence = st.session_state.get('example_sentence', 'No example available')
    example_sentence_display = html.escape(str(example_sentence)) if example_sentence else "No example available"

    # Progress indicator
    st.markdown(f"<p style='text-align: center; color: rgba(255,255,255,0.7); margin-bottom: 0.5rem;'>{st.session_state.word_index + 1} / {len(saved_words)}</p>", unsafe_allow_html=True)

    # Card HTML
    card_html = f"""
    <div class="vocab-card">
        <div class="word-section">
            <span class="word-text">{current_word_display}</span>
            <p class="meaning-text">Meaning: {current_meaning_display}</p>
        </div>
        <div class="example-section">
            <p class="example-label">Example Sentence:</p>
            <p class="example-text">{example_sentence_display}</p>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    st.write("")  # spacing

    # Action buttons row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔊 Play", use_container_width=True):
            play_audio_mobile_compatible(example_sentence)

    with col2:
        if st.button("◀ Previous", use_container_width=True):
            st.session_state.word_index -= 1
            if st.session_state.word_index < 0:
                st.session_state.word_index = len(saved_words) - 1
            st.rerun()

    with col3:
        if st.button("Next ▶", use_container_width=True):
            st.session_state.word_index += 1
            if st.session_state.word_index >= len(saved_words):
                st.session_state.word_index = 0
            st.rerun()

    with col4:
        if st.button("🗑 Delete", use_container_width=True):
            try:
                supabase_client.delete_saved_word(current_word)
                saved_words_data = supabase_client.get_all_saved_words()
                saved_words = [(item['word'], item['meaning'], item.get('added_on', '')) for item in saved_words_data]
                if len(saved_words) > 0:
                    st.session_state.word_index = min(st.session_state.word_index, len(saved_words) - 1)
                else:
                    st.session_state.word_index = 0
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
