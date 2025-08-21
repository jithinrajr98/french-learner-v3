import streamlit as st
from pathlib import Path
from config.settings import BACKGROUND
import base64

# ====== STYLE CONFIGURATION ======
def set_page_config():
    st.set_page_config(
        page_title="French Learner",
        page_icon="🇫🇷",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def apply_custom_styles():
    """Modern, elegant theme with purple gradient background inspired by the NixtNode design"""
    french_blue = "#2C3E91"  # Deep French blue
    french_red = "#ED2939"   # French flag red
    slate_gray = "#4A4A4A"   # Elegant text color
    
    st.markdown(f"""
    <style>
        /* Main app container matching your gradient image */
        .stApp {{
            background: url('data:image/jpeg;base64,{get_base64_of_bin_file(BACKGROUND)}') no-repeat center center fixed;
            color: white;
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
        }}
        
        /* Add overlay pattern for depth */
        .stApp::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(255,255,255,0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255,255,255,0.08) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(255,255,255,0.05) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }}
        
        /* MAKE HEADER COMPLETELY TRANSPARENT */
        .stApp > header {{
            background-color: transparent !important;
            background: transparent !important;
        }}
        
        /* Remove any padding/margin that might create visual space */
        .stApp > header > div {{
            padding: 0 !important;
            margin: 0 !important;
            background: transparent !important;
        }}
        
        /* Make the header toolbar buttons transparent too */
        .stApp > header > div > div {{
            background: transparent !important;
        }}
        
        /* Floating sidebar with glass morphism */
        [data-testid="stSidebar"] {{
            background: rgba(0, 0, 0, 0.4) !important;
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 0 20px 20px 0;
            margin: 10px 0 10px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        
        /* Make sidebar content float */
        [data-testid="stSidebar"] > div {{
            padding-top: 20px;
        }}
        
        /* Floating main content area */
        .main .block-container {{
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(15px) saturate(150%);
            -webkit-backdrop-filter: blur(15px) saturate(150%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            margin: 20px;
            padding: 30px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
        }}
        
        /* Enhanced navigation menu items with floating effect */
        div[role=radiogroup] > label {{
            margin: 8px 0;
            padding: 14px 18px;
            border-radius: 15px;
            background: rgba(255,255,255,0.1);
            color: white !important;
            transition: all 0.4s ease;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }}
        
        div[role=radiogroup] > label:hover {{
            background: rgba(255,255,255,0.2);
            transform: translateX(6px) translateY(-2px);
            border: 1px solid rgba(255,255,255,0.3);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        }}
        
        div[role=radiogroup] > [data-baseweb="radio"]:checked + label {{
            background: linear-gradient(135deg, {french_red} 0%, #ff6b9d 100%);
            font-weight: 500;
            border: 1px solid rgba(255,255,255,0.4);
            transform: translateX(8px);
            box-shadow: 0 10px 30px rgba(237, 41, 57, 0.3);
        }}
        
        /* Enhanced buttons with floating effect */
        .stButton > button {{
            border-radius: 15px;
            padding: 14px 28px;
            background: rgba(255,255,255,0.1);
            color: white;
            border: 1px solid rgba(255,255,255,0.2);
            font-weight: 500;
            transition: all 0.4s ease;
            backdrop-filter: blur(15px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .stButton > button:hover {{
            background: rgba(255,255,255,0.2);
            transform: translateY(-4px);
            box-shadow: 0 12px 35px rgba(168, 85, 247, 0.4);
            border: 1px solid rgba(255,255,255,0.4);
        }}
        
        header[data-testid="stHeader"] {{
            background: transparent !important;
            background-color: transparent !important;
        }}
        
        header[data-testid="stHeader"] > div {{
            background: transparent !important;
            background-color: transparent !important;
        }}
        
        div[data-testid="stToolbar"] {{
            background: transparent !important;
            background-color: transparent !important;
        }}
        
        /* Optional: Style toolbar buttons to match your theme */
        div[data-testid="stToolbar"] button {{
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: white !important;
            backdrop-filter: blur(10px);
        }}
        
        /* Headers with improved visibility */
        h1 {{
            color: white;
            font-weight: 600;
            letter-spacing: -0.5px;
            margin-bottom: 2.5rem;
            padding-bottom: 20px;
            font-size: 2rem !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        h2 {{
            color: white;
            font-weight: 500;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            padding-bottom: 8px;
            margin-top: 1.5rem;
            font-size: 1.3rem !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        }}
        
        /* Input fields with glass effect */
        .stTextArea textarea, .stTextInput input {{
            border-radius: 12px;
            padding: 14px;
            background: rgba(255,255,255,0.1) !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            color: white !important;
            backdrop-filter: blur(10px);
        }}
        
        .stTextArea textarea::placeholder, .stTextInput input::placeholder {{
            color: rgba(255,255,255,0.6) !important;
        }}
        
        /* Cards with glass morphism */
        .card {{
            background: rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
            font-size: 1.0rem !important;
        }}
        
        /* Feedback section */
        .feedback {{
            background: rgba(255,255,255,0.15);
            border-left: 4px solid rgba(255,255,255,0.4);
            padding: 20px;
            border-radius: 0 12px 12px 0;
            margin: 20px 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        /* Score display */
        .score {{
            font-size: 1.8rem;
            font-weight: 700;
            color: white;
            text-align: center;
            margin: 20px 0;
            padding: 16px;
            background: rgba(255,255,255,0.15);
            border-radius: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        /* Word cards */
        .word-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 14px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
        }}
        
        .word-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(168, 85, 247, 0.2);
            background: rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.25);
        }}
        
        /* Text color adjustments for better contrast */
        .stMarkdown, .stText, p, div {{
            color: white !important;
        }}
        
        /* Selectbox and other inputs */
        .stSelectbox > div > div {{
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
        }}
        
        /* Radio button text */
        [data-testid="stRadio"] > div {{
            color: white !important;
        }}
        
        /* Custom scrollbar for the new theme */
        ::-webkit-scrollbar {{
            width: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(255,255,255,0.1);
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: rgba(255,255,255,0.3);
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255,255,255,0.5);
        }}
        
    </style>
    """, unsafe_allow_html=True)

# ====== UI COMPONENTS ======
def header_section():
    """Elegant header with a new horizontal stripe design and French flag"""
    st.markdown(f"""
    <div style="margin-top: 10px; display: flex; align-items: left;">
        <h1 style="margin-bottom: 0; padding-top: 0; display: inline-block;">Limiting Factor</h1>
        <div style="margin-left: 0px; margin-top: 0px; display: flex; flex-direction: column; align-items: flex-start;">
            <div style="height: 5px; background-color: #ED2939; width: 130px; margin: 4px 0; border-radius: 3px;"></div>
            <div style="height: 5px; background-color: #FFFFFF; width: 100px; margin: 4px 0; border-radius: 3px;"></div>
            <div style="height: 5px; background-color: #2C3E91; width: 50px; margin: 4px 0; border-radius: 3px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def sidebar_navigation():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 30px; padding: 20px 0;">
            <h2 style="color: white; font-size: 1.5rem; margin-bottom: 8px;">📚 Navigation</h2>
            <div style="height: 2px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); margin: 0 20px;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Put widgets inside a container
        with st.container():
            page = st.radio(
                "",  # No label
                ["Writing", "Vocabulary", "Practice Vocabulary", "Transcript Viewer", "Progress Tracker"],
                label_visibility="collapsed"
            )

        st.markdown("""
        <div style="margin-top: 40px;">
            <div style="height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); margin: 20px 0;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px; font-size: 0.9rem; color: rgba(255,255,255,0.6);">
            <small>Built with ❤️ by Jithin</small>
        </div>
        """, unsafe_allow_html=True)

    return page
