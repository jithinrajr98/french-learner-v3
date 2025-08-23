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
            'input_method': 'text'  # 'text' or 'audio'
        })
    
    # Enhanced CSS
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
            border-left: 4px solid #10B981;
        }
        .score-badge {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 1rem;
        }
        .input-method-toggle {
            margin: 1rem 0;
        }
        .audio-status {
            padding: 0.5rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.divider()
    # Header
    st.markdown("#### 📝 Writing Practice")
    st.caption("Translate the following English sentence into French. You can type or speak your translation!")

    # English prompt
    st.markdown(f'<div class="english-text">{st.session_state.current_pair[0]}</div>', unsafe_allow_html=True)
    
    # Input method selector
    st.markdown("**Choose input method:**")
    input_method = st.radio(
        "Input method",
        ["Type translation", "Speak translation"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    user_input = ""
    
    if input_method == "Type translation":
        # Text input (original functionality)
        user_input = st.text_area(
            "**Enter your French translation:**",
            value=st.session_state.user_translation,
            height=100,
            placeholder="Write your translation here...",
            label_visibility="visible"
        )
    
    else:
        # Audio input
        st.markdown("**Speak your French translation:**")
        
        # Audio recorder widget
        audio_file = st.audio_input("Record your translation")
        
        if audio_file:
            # Show processing status
            with st.spinner("Converting speech to text..."):
                transcribed_text = audio_to_text(audio_file)
            
            # Display transcribed text
            if transcribed_text and not transcribed_text.startswith(("Could not understand", "Speech recognition error", "Error processing")):
                st.success(f"Transcribed: {transcribed_text}")
                user_input = transcribed_text
                # Update session state with transcribed text
                st.session_state.user_translation = transcribed_text
            else:
                st.error(transcribed_text)
                
        # Show current transcription for editing if needed
        if st.session_state.user_translation:
            user_input = st.text_area(
                "**Edit transcribed text (if needed):**",
                value=st.session_state.user_translation,
                height=80,
                help="You can edit the transcribed text if it's not accurate"
            )
    
    # Buttons row
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("✅ Check", use_container_width=True):
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
                    save_missing_words(missed)
                save_score(st.session_state.current_pair[0], user_input, st.session_state.score)
                
                st.rerun()
            else:
                st.warning("Please enter or speak a translation")
    
    with col2:
        if st.button("🔄 Try New", use_container_width=True):
            en, fr = transcript_manager.get_random_pair()
            st.session_state.current_pair = (en, fr)
            st.session_state.user_translation = ""
            st.session_state.feedback = ""
            st.session_state.checked = False
            st.session_state.score = 0
            st.rerun()
    
    # Results display (unchanged from original)
    if st.session_state.checked:
        st.divider()
        # Session info
        st.caption(f"Attempt #{st.session_state.attempt_count}")
        
        # Score with color coding
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
        
        st.markdown(f'<div class="score-badge" style="background: {color}20; color: {color};">{emoji} Score: {score}/10</div>', unsafe_allow_html=True)
        
        # Comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Your translation:**")
            st.info(st.session_state.user_translation)
        
        with col2:
            st.write("**Correct translation:**")
            st.success(st.session_state.current_pair[1])
        
        if st.button("🔊 Pronunciation", help="Hear correct pronunciation"):
            play_audio_mobile_compatible(st.session_state.current_pair[1])
        
        st.divider()

        # Feedback
        if st.session_state.feedback:
            st.write("**Feedback:**")
            st.write(st.session_state.feedback)

# Optional: Add this if you want to test the component standalone
if __name__ == "__main__":
    writing()