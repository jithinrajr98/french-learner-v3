import base64
from gtts import gTTS
import io
import streamlit as st


def play_audio_mobile_compatible(text, lang='fr', speed=1.25):
    """
    Generate and play audio with mobile compatibility at the requested
    playback rate (HTML5 `playbackRate`, applied client-side).

    `speed` defaults to 1.25 to preserve the historical behaviour of this
    helper for callers that don't care.
    """
    # Sanity-clamp so a stray value can't blow up the <audio> element.
    try:
        PLAYBACK_SPEED = float(speed)
    except (TypeError, ValueError):
        PLAYBACK_SPEED = 1.25
    PLAYBACK_SPEED = max(0.25, min(4.0, PLAYBACK_SPEED))

    try:
        # Generate TTS audio
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        # Convert to base64 for better mobile compatibility
        audio_base64 = base64.b64encode(audio_bytes.read()).decode()
        
        # Create custom HTML audio player with better mobile support and configurable playback rate
        audio_html = f"""
        <audio controls autoplay style="width: 100%; margin: 10px 0;" playbackRate="{PLAYBACK_SPEED}">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg">
            <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
            Your browser does not support the audio element.
        </audio>
        <script>
            // Set playback rate to {PLAYBACK_SPEED}x after audio loads
            document.addEventListener('DOMContentLoaded', function() {{
                const audioElements = document.querySelectorAll('audio');
                audioElements.forEach(function(audio) {{
                    audio.addEventListener('loadeddata', function() {{
                        audio.playbackRate = {PLAYBACK_SPEED};
                    }});
                    // Also set it immediately in case audio is already loaded
                    if (audio.readyState >= 2) {{
                        audio.playbackRate = {PLAYBACK_SPEED};
                    }}
                }});
            }});
        </script>
        """
        
        st.markdown(audio_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Couldn't generate audio: {e}")
