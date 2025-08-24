import streamlit as st
from core.evaluation import check_translation
from core.database import save_score, save_missing_words
from core.llm_utils import LLMUtils
from core.audio import play_audio, play_audio_mobile_compatible
from core.transcript_processing import TranscriptManager
import speech_recognition as sr
import io
import tempfile
import os
from core.database_supabase import SupabaseDB

supabase_client = SupabaseDB()

llm_utils = LLMUtils()
transcript_manager = TranscriptManager()

def audio_to_text(audio_file):
    """Convert audio file to text using speech recognition"""
    try:
        # Handle UploadedFile object
        if hasattr(audio_file, 'read'):
            audio_bytes = audio_file.read()
        else:
            audio_bytes = audio_file
            
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Load audio file
        with sr.AudioFile(temp_audio_path) as source:
            audio = recognizer.record(source)
        
        # Convert to text (you can change language to 'fr-FR' for French)
        text = recognizer.recognize_google(audio, language='fr-FR')
        
        # Clean up temp file
        os.unlink(temp_audio_path)
        
        return text
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError as e:
        return f"Speech recognition error: {e}"
    except Exception as e:
        return f"Error processing audio: {e}"

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
            'attempt_count': 0,
            'input_method': 'text'
        })
    
    # Enhanced CSS for cleaner UI
    st.markdown("""
    <style>
        .main-container {
            max-width: 800px;
            margin: 0 auto;
        }
        .english-text {
            font-size: 1.3rem;
            font-weight: 500;
            color: white;
            margin: 2rem 0;
            padding: 2rem;
            background: rgba(255,255,255,0.1);
            border-radius: 16px;
            border-left: 4px solid #10B981;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .score-badge {
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            display: inline-block;
            margin: 1rem 0;
            font-size: 1.1rem;
        }
        .input-section {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .method-selector {
            margin-bottom: 1.5rem;
        }
        .button-row {
            margin: 2rem 0 1rem 0;
            gap: 1rem;
        }
        .results-section {
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 2px solid rgba(255,255,255,0.1);
        }
        .translation-comparison {
            margin: 1.5rem 0;
        }
        .feedback-section {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 1.5rem;
        }
        .header-section {
            text-align: center;
            margin-bottom: 2rem;
        }
        .pronunciation-button {
            margin: 1rem 0;
            text-align: center;
        }
        .attempt-counter {
            text-align: center;
            opacity: 0.7;
            margin-bottom: 1rem;
        }
        /* Clean up default Streamlit spacing */
        .stRadio > div {
            gap: 2rem;
        }
        .stButton > button {
            height: 3rem;
            border-radius: 8px;
            font-weight: 500;
        }
        .stTextArea > div > div > textarea {
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Clean header section
    st.markdown('<div class="header-section">', unsafe_allow_html=True)
    st.markdown("#### 📝 Writing Practice")
    st.markdown("**Translate the English sentence into French**")
    st.markdown('</div>', unsafe_allow_html=True)

    # English prompt in a clean container
    st.markdown(f'<div class="english-text">{st.session_state.current_pair[0]}</div>', unsafe_allow_html=True)
    
    # Input section with cleaner styling
    
    # Method selector with better spacing
    st.markdown('<div class="method-selector">', unsafe_allow_html=True)
    input_method = st.radio(
        "**Choose how to input your translation:**",
        ["Type translation", "Speak translation"],
        horizontal=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    user_input = ""
    
    if input_method == "Type translation":
        user_input = st.text_area(
            "**Your French translation:**",
            value=st.session_state.user_translation,
            height=120,
            placeholder="Écrivez votre traduction ici...",
            help="Type your French translation in the text box above"
        )
    
    else:
        st.markdown("**Record your French translation:**")
        audio_file = st.audio_input("🎤 Click to record")
        
        if audio_file:
            with st.spinner("🔄 Converting speech to text..."):
                transcribed_text = audio_to_text(audio_file)
            
            if transcribed_text and not transcribed_text.startswith(("Could not understand", "Speech recognition error", "Error processing")):
                st.success(f"✅ **Transcribed:** {transcribed_text}")
                user_input = transcribed_text
                st.session_state.user_translation = transcribed_text
            else:
                st.error(f"❌ {transcribed_text}")
                
        if st.session_state.user_translation:
            user_input = st.text_area(
                "**Edit if needed:**",
                value=st.session_state.user_translation,
                height=80,
                help="Fine-tune the transcribed text if necessary"
            )
    
    
    # Action buttons with better spacing
    st.markdown('<div class="button-row">', unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        check_clicked = st.button("✅ Check Translation", use_container_width=True, type="primary")
    
    with col2:
        new_clicked = st.button("🔄 Try New Sentence", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle button clicks
    if check_clicked:
        if user_input and user_input.strip():
            st.session_state.user_translation = user_input
            st.session_state.feedback, st.session_state.score = check_translation(
                st.session_state.current_pair[0],
                user_input,
                st.session_state.current_pair[1]
            )
            st.session_state.attempt_count += 1
            st.session_state.checked = True
            
            # Save results
            missed = llm_utils.extract_missed_words(st.session_state.current_pair[1], user_input)
            if missed:
                supabase_client.save_missing_words(missed)
            supabase_client.save_score(st.session_state.current_pair[0], user_input, st.session_state.score)
            
            st.rerun()
        else:
            st.warning("⚠️ Please enter or speak a translation before checking")
    
    if new_clicked:
        en, fr = transcript_manager.get_random_pair()
        st.session_state.current_pair = (en, fr)
        st.session_state.user_translation = ""
        st.session_state.feedback = ""
        st.session_state.checked = False
        st.session_state.score = 0
        st.rerun()
    
    # Results section with cleaner layout
    if st.session_state.checked:
        st.markdown('<div class="results-section">', unsafe_allow_html=True)
        
        # Attempt counter
        st.markdown(f'<div class="attempt-counter">Attempt #{st.session_state.attempt_count}</div>', unsafe_allow_html=True)
        
        # Score display with better styling
        score = st.session_state.score
        if score >= 8:
            color = "#10B981"
            emoji = "🎉"
            message = "Excellent!"
        elif score >= 6:
            color = "#F59E0B"
            emoji = "👍"
            message = "Good job!"
        else:
            color = "#EF4444"
            emoji = "💪"
            message = "Keep practicing!"
        
        st.markdown(f'''
        <div style="text-align: center;">
            <div class="score-badge" style="background: {color}20; color: {color};">
                {emoji} Score: {score}/10 - {message}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Translation comparison with cleaner layout
        st.markdown('<div class="translation-comparison">', unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown("**Your Translation:**")
            st.info(st.session_state.user_translation)
        
        with col2:
            st.markdown("**Correct Translation:**")
            st.success(st.session_state.current_pair[1])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Pronunciation button
        st.markdown('<div class="pronunciation-button">', unsafe_allow_html=True)
        if st.button("🔊 Listen to Pronunciation", help="Hear the correct pronunciation", use_container_width=False):
            play_audio_mobile_compatible(st.session_state.current_pair[1])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Feedback section
        # Feedback section
        if st.session_state.feedback:
            st.markdown("**Feedback:**")
            # Display feedback with proper bullet point formatting
            for line in st.session_state.feedback.split('\n'):
                if line.strip():  # Only show non-empty lines
                    st.warning(f":warning: {line}")
                    
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Optional: Add this if you want to test the component standalone
if __name__ == "__main__":
    writing()