from config.styles import apply_custom_styles, header_section, sidebar_navigation, set_page_config
import streamlit as st
def main():
    set_page_config()
    apply_custom_styles()
    header_section()
    current_page = sidebar_navigation()
    
    st.write(f"Current page: {current_page}")  # For demonstration

if __name__ == "__main__":
    main()