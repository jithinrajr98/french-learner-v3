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
        
        
def record_audio(duration=5, sample_rate=44100, chunk_size=1024):
    """
    Record audio from the user's microphone
    Returns audio bytes if successful, None otherwise
    """
    try:
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Open stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size
        )
        
        st.info(f"Recording for {duration} seconds... Speak now!")
        
        frames = []
        
        # Record audio
        for i in range(0, int(sample_rate / chunk_size * duration)):
            data = stream.read(chunk_size)
            frames.append(data)
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save to in-memory WAV file
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
        
        wav_buffer.seek(0)
        return wav_buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error recording audio: {e}")
        return None

