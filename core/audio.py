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