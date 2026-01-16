import streamlit as st
from core.evaluation import check_translation, scorer
from core.database_supabase import SupabaseDB
from core.llm_utils import LLMUtils
from core.transcript_processing import TranscriptManager
from core.audio import play_audio

supabase_client = SupabaseDB()
llm_utils = LLMUtils()
transcript_manager = TranscriptManager()

def writing():
    # Initialize session state
    if 'current_pair' not in st.session_state:
        en, fr = transcript_manager.get_random_pair()
        st.session_state.update({
            'current_pair': (en, fr),
            'user_translation': "",
            'feedback': "",
            'checked': False,
            'score': 0,
            'attempt_count': 0
        })

    # Minimalist CSS
    st.markdown("""
    <style>
        /* Header bar - centered, clean */
        .practice-header {
            background: linear-gradient(135deg, #3B5998 0%, #4A69BD 100%);
            color: white;
            padding: 14px 24px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 24px;
            box-shadow: 0 4px 15px rgba(59, 89, 152, 0.4);
        }

        .practice-header h2 {
            margin: 0;
            font-size: 1.2rem;
            font-weight: 600;
            color: white !important;
            border: none;
            padding: 0;
        }

        /* Sentence display */
        .sentence-display {
            font-size: 1.15rem;
            color: #90CAF9 !important;
            font-style: italic;
            padding: 20px 0;
            text-align: center;
            margin-bottom: 16px;
        }

        /* Compact feedback line */
        .feedback-line {
            text-align: center;
            padding: 12px 0;
            margin: 16px 0;
        }

        .feedback-success-text {
            color: #81C784 !important;
            font-size: 1.1rem;
            font-weight: 600;
        }

        .feedback-warning-text {
            color: #FFB74D !important;
            font-size: 1.1rem;
            font-weight: 600;
        }

        /* Correct translation display */
        .correct-translation-box {
            background: rgba(59, 89, 152, 0.2);
            border-radius: 8px;
            padding: 14px 20px;
            margin: 16px 0;
            text-align: center;
        }

        .correct-translation-text {
            color: #90CAF9 !important;
            font-size: 1.05rem;
            font-weight: 500;
            margin: 0;
        }

        /* Submit button - orange */
        .submit-btn button {
            background: #E67E22 !important;
            color: white !important;
            border: none !important;
            border-radius: 20px !important;
            padding: 8px 20px !important;
            font-weight: 500 !important;
        }

        .submit-btn button:hover {
            background: #D35400 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(230, 126, 34, 0.4);
        }

        /* Skip/ghost button */
        .skip-btn button {
            background: transparent !important;
            color: rgba(255,255,255,0.7) !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            border-radius: 20px !important;
            padding: 8px 20px !important;
            font-weight: 500 !important;
        }

        .skip-btn button:hover {
            background: rgba(255,255,255,0.1) !important;
            border-color: rgba(255,255,255,0.5) !important;
        }

        /* Blue action buttons */
        .blue-btn button {
            background: #3B5998 !important;
            color: white !important;
            border: none !important;
            border-radius: 20px !important;
            padding: 8px 20px !important;
            font-weight: 500 !important;
        }

        .blue-btn button:hover {
            background: #2D4373 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 89, 152, 0.4);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header bar
    st.markdown("""
    <div class="practice-header">
        <h2>French Writing Practice</h2>
    </div>
    """, unsafe_allow_html=True)

    # Sentence to translate
    st.markdown(f'<p class="sentence-display">"{st.session_state.current_pair[0]}"</p>', unsafe_allow_html=True)

    # Translation input
    user_input = st.text_area(
        "",
        value=st.session_state.user_translation,
        height=100,
        placeholder="Type your French translation...",
        key="translation_input",
        label_visibility="collapsed"
    )

    # Button row: Skip and Submit
    if not st.session_state.checked:
        col1, col2, col3 = st.columns([2, 1, 1])

        with col2:
            st.markdown('<div class="skip-btn">', unsafe_allow_html=True)
            skip_clicked = st.button("Skip →", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="submit-btn">', unsafe_allow_html=True)
            check_clicked = st.button("Submit", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Handle skip
        if skip_clicked:
            en, fr = transcript_manager.get_random_pair()
            st.session_state.current_pair = (en, fr)
            st.session_state.user_translation = ""
            st.session_state.feedback = ""
            st.session_state.checked = False
            st.session_state.score = 0
            st.rerun()

        if check_clicked:
            if user_input and user_input.strip():
                st.session_state.user_translation = user_input
                st.session_state.feedback = check_translation(
                    st.session_state.current_pair[0],
                    user_input,
                    st.session_state.current_pair[1]
                )
                st.session_state.attempt_count += 1
                st.session_state.checked = True

                # Calculate score
                st.session_state.score = scorer(user_input, st.session_state.current_pair[1])

                # Save results
                missed = llm_utils.extract_missed_words(st.session_state.current_pair[1], user_input)
                if missed:
                    supabase_client.save_missing_words(missed)
                supabase_client.save_score(st.session_state.current_pair[0], user_input, st.session_state.score)

                st.rerun()
            else:
                st.warning("Please type your translation")

    # Results section
    if st.session_state.checked:
        score = st.session_state.score

        # Compact feedback line
        if score >= 8:
            st.markdown(f'<div class="feedback-line"><span class="feedback-success-text">✓ Great! {score}/10</span></div>', unsafe_allow_html=True)
        elif score >= 5:
            st.markdown(f'<div class="feedback-line"><span class="feedback-warning-text">Good effort! {score}/10</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="feedback-line"><span class="feedback-warning-text">Keep practicing! {score}/10</span></div>', unsafe_allow_html=True)

        # Show correct translation directly
        st.markdown(f"""
        <div class="correct-translation-box">
            <p class="correct-translation-text">{st.session_state.current_pair[1]}</p>
        </div>
        """, unsafe_allow_html=True)

        # Two buttons side by side: Listen and Next
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col2:
            st.markdown('<div class="skip-btn">', unsafe_allow_html=True)
            if st.button("🔊 Listen", use_container_width=True):
                play_audio(st.session_state.current_pair[1])
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="blue-btn">', unsafe_allow_html=True)
            if st.button("Next →", use_container_width=True):
                en, fr = transcript_manager.get_random_pair()
                st.session_state.current_pair = (en, fr)
                st.session_state.user_translation = ""
                st.session_state.feedback = ""
                st.session_state.checked = False
                st.session_state.score = 0
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# Optional: Add this if you want to test the component standalone
if __name__ == "__main__":
    writing()