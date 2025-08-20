from core.transcript_processing import TranscriptManager
import streamlit as st
from config.settings import TRANSCRIPT_YOUTUBE, TRANSCRIPT_EN, TRANSCRIPT_FR
from core.llm_utils import LLMUtils

llm_utils = LLMUtils()
transcript_manager = TranscriptManager()

def transcript_render():
    st.markdown("<h1 style='text-align: center;'>📄 YouTube Transcript Extractor</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Use a single expander for the entire video processing section to keep it tidy
    with st.expander("🎥 Process a New YouTube Video"):
        video_id = st.text_input("Enter YouTube Video ID:", placeholder="e.g., gUdkxWNJTr0")

        if st.button("Extract and Process Transcript", use_container_width=True):
            if not video_id:
                st.warning("Please enter a video ID.")
                return

            st.info("Processing transcript... This may take a moment.")
            
            try:
                # Step 1: Extract the YouTube transcript
                transcript_manager.extract_transcript(video_id)
                st.success("✅ Transcript extracted successfully!")
                
                # Step 2: Generate French sentences
                transcript = transcript_manager.load_youtube_transcript(TRANSCRIPT_YOUTUBE)
                french_sentences = llm_utils.youtube_french_sentence_generator(transcript)
                with open(TRANSCRIPT_FR, "w", encoding="utf-8") as file:
                    file.write(french_sentences)
                st.success("✅ French sentences generated!")

                # Step 3: Generate English translations
                english_sentences = llm_utils.youtube_english_sentence_generator(french_sentences)
                with open(TRANSCRIPT_EN, "w", encoding="utf-8") as file:
                    file.write(english_sentences)
                st.success("✅ English translations generated!")
            
            except FileNotFoundError:
                st.error("Error: Transcript file not found.")
            except Exception as e:
                st.error(f"An error occurred during processing: {str(e)}")
    
    st.markdown("---")

    st.header("📜 Transcript Viewer")
    
    # Use columns to align the buttons side-by-side
    col1, col2 = st.columns(2)
    
    # Use session state to manage which transcript to display
    if 'display_transcript' not in st.session_state:
        st.session_state.display_transcript = None
        
    with col1:
        if st.button("Show French Transcript", use_container_width=True):
            st.session_state.display_transcript = 'fr'
            
    with col2:
        if st.button("Show English Transcript", use_container_width=True):
            st.session_state.display_transcript = 'en'
    
    if st.session_state.display_transcript:
        try:
            if st.session_state.display_transcript == 'fr':
                file_path = TRANSCRIPT_FR
                title = "French Transcript"
            else:
                file_path = TRANSCRIPT_EN
                title = "English Transcript"
            
            transcript_content = transcript_manager.load_youtube_transcript(file_path)
            st.subheader(title)
            st.text_area("Content", value=transcript_content, height=500, key=title)
        except FileNotFoundError:
            st.error("Transcript file not found. Please process a video first.")