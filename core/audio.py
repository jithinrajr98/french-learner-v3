import base64
from gtts import gTTS
import io
import base64
from IPython.display import Audio
import streamlit as st

  
def play_audio(text, lang='fr'):
    """Generate and play audio for given text"""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format='audio/mp3')
    except Exception as e:
        st.error(f"Couldn't generate audio: {e}")        
        
def play_audio_mobile_compatible(text, lang='fr'):
    """Generate and play audio with mobile compatibility"""
    try:
        # Generate TTS audio
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        # Convert to base64 for better mobile compatibility
        audio_base64 = base64.b64encode(audio_bytes.read()).decode()
        
        # Create custom HTML audio player with better mobile support
        audio_html = f"""
        <audio controls autoplay style="width: 100%; margin: 10px 0;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg">
            <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
            Your browser does not support the audio element.
        </audio>
        """
        
        st.markdown(audio_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Couldn't generate audio: {e}")