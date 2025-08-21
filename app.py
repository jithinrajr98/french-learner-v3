from config.styles import apply_custom_styles, header_section, sidebar_navigation, set_page_config
from core.database import init_db
from config.settings import DB_PATH
import streamlit as st
from page_modules.writing_practise import writing
from page_modules.vocab_builder import vocab_builder
from page_modules.vocab_practise import vocab_practise
from page_modules.transcript_viewer import transcript_render
from page_modules.performance_analyser import analyse

import warnings
warnings.filterwarnings("ignore")


def main():
    set_page_config()
    apply_custom_styles()
    init_db(DB_PATH)
    header_section()
    
    # Get selected page from sidebar navigation
    page = sidebar_navigation()
    
    # Use elif instead of multiple if statements for better performance
    if page == "Writing":
        writing()
    elif page == "Vocabulary":
        vocab_builder()
    elif page == "Practice Vocabulary":
        vocab_practise()
    elif page == "Transcript Viewer":
        transcript_render()
    elif page == "Progress Tracker":
        analyse()
    else:
        # Fallback - should never happen but good to have
        st.error("Page not found!")

if __name__ == "__main__":
    main()