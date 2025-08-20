from config.styles import apply_custom_styles, header_section, sidebar_navigation, set_page_config
from core.database import init_db
from config.settings import DB_PATH
import streamlit as st
from pages.writing_practise import writing
import warnings
warnings.filterwarnings("ignore")


def main():
    set_page_config()
    apply_custom_styles()
    init_db(DB_PATH)
    header_section()
    page = sidebar_navigation()
    
    if page == "Practice":
        writing()
   
   

if __name__ == "__main__":
    main()