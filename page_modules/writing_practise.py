import streamlit as st
from core.evaluation import check_translation, scorer
from core.database_supabase import SupabaseDB
from core.llm_utils import LLMUtils
from core.transcript_processing import TranscriptManager

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
    
    # Simplified CSS for cleaner UI
    st.markdown("""
    <style>
        .english-text {
            font-size: 1.2rem;
            font-weight: 400;
            color: white;
            margin: 1rem 0;
            padding: 1rem;
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            border-left: 4px solid #10B981;
            text-align: left;
        }
        .score-badge {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            display: inline-block;
            margin: 1rem 0;
        }
        .button-row {
            display: flex;
            gap: 1rem;
            margin: 1.5rem 0;
        }
        .translation-comparison {
            margin: 1.5rem 0;
        }
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header section
    st.markdown("#### 📝 Writing Practice")
    st.markdown("Translate the English sentence into French")
    
    # English prompt
    st.markdown(f'<div class="english-text">{st.session_state.current_pair[0]}</div>', unsafe_allow_html=True)
    
    # Text input for translation
    user_input = st.text_area(
        "**Your French translation:**",
        value=st.session_state.user_translation,
        height=100,
        placeholder="Type your translation here...",
        key="translation_input"
    )
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        check_clicked = st.button("✅ Evaluate", use_container_width=True, type="primary")
    
    with col2:
        new_clicked = st.button("🔄 New Sentence", use_container_width=True)
    
    # Handle button clicks
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
            print(st.session_state.feedback)
            
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
    
    if new_clicked:
        en, fr = transcript_manager.get_random_pair()
        st.session_state.current_pair = (en, fr)
        st.session_state.user_translation = ""
        st.session_state.feedback = ""
        st.session_state.checked = False
        st.session_state.score = 0
        st.rerun()
    
    # Results section
    if st.session_state.checked:
        st.divider()
        
        # Score display
        score = st.session_state.score
        if score >= 8:
            color = "#10B981"
            emoji = "🎉"
        elif score >= 6:
            color = "#F59E0B"
            emoji = "👍"
        else:
            color = "#EF4444"
            emoji = "💪"
        
        st.markdown(f'''
        <div style="text-align: center;">
            <div class="score-badge" style="background: {color}20; color: {color};">
                {emoji} Score: {score}/10
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Translation comparison
        st.markdown('<div class="translation-comparison">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Your Translation:**")
            st.info(st.session_state.user_translation)
        
        with col2:
            st.markdown("**Correct Translation:**")
            st.success(st.session_state.current_pair[1])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Feedback section
        if st.session_state.feedback:
            st.markdown("**Feedback:**")
            for line in st.session_state.feedback.split('\n'):
                if line.strip():
                    st.warning(f"• {line}")

# Optional: Add this if you want to test the component standalone
if __name__ == "__main__":
    writing()