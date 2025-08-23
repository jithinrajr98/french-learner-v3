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
    
    # Initialize databases
    try:
        # Initialize SQLite database (for fallback or local development)
        init_db(DB_PATH)
        
        # Initialize Supabase connection
        try:
            from core.database_supabase import SupabaseDB
            supabase_client = SupabaseDB()
            
            # Test Supabase connection
            test_words = supabase_client.get_all_saved_words()
            st.session_state.db_status = "supabase"
            
        except ImportError as import_error:
            st.warning(f"Supabase module import failed: {import_error}. Using local database.")
            st.session_state.db_status = "local"
        except Exception as supabase_error:
            st.warning(f"Supabase connection failed: {supabase_error}. Using local database.")
            st.session_state.db_status = "local"
            
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        st.session_state.db_status = "error"
        return
    
    header_section()
    
    # Display database status in sidebar (optional for debugging)
    # if st.session_state.get('db_status') == 'supabase':
    #     st.sidebar.success("🌐 Connected to Supabase")
    # elif st.session_state.get('db_status') == 'local':
    #     st.sidebar.info("💾 Using local database")
    # elif st.session_state.get('db_status') == 'error':
    #     st.sidebar.error("❌ Database error")
    
    # Get selected page from sidebar navigation
    page = sidebar_navigation()
    
    # Route to appropriate page functions
    try:
        if page == "Practise Writing":
            writing()
        elif page == "Explore Vocabulary":
            vocab_builder()
        elif page == "Practise Vocabulary":
            vocab_practise()
        elif page == "Update Transcript":
            transcript_render()
        elif page == "Progress Tracker":
            analyse()
        else:
            # Fallback - should never happen but good to have
            st.error("Page not found!")
            
    except Exception as page_error:
        st.error(f"Error loading page '{page}': {page_error}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

if __name__ == "__main__":
    main()