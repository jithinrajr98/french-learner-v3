from config.styles import apply_custom_styles, header_section, sidebar_navigation, set_page_config
from core.database import init_db
from config.settings import DB_PATH
import streamlit as st
from pages.writing_practise import writing
from pages.vocab_builder import vocab_builder
from pages.vocab_practise import vocab_practise
from pages.transcript_viewer import transcript_render
from pages.performance_analyser import analyse

import warnings
warnings.filterwarnings("ignore")


def main():
    set_page_config()
    apply_custom_styles()
    init_db(DB_PATH)
    header_section()
    page = sidebar_navigation()
    
    if page == "Writing":
        writing()
    if page == "Vocabulary":
        vocab_builder()
    if page == "Practice Vocabulary":
        vocab_practise()

    if page == "Transcript Viewer":
        transcript_render()
        
    if page ==  "Progress Tracker":
        analyse()   
   

if __name__ == "__main__":
    main()