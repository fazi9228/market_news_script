import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", message="No secrets found")

# --- Page Configuration ---
# MOVED TO THE TOP: This must be the first Streamlit command to run.
st.set_page_config(
    page_title="Market News Content Generator",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Step 1: Load API Keys with Better Error Handling ---
def load_api_keys():
    """
    Loads API keys from Streamlit secrets if deployed, otherwise from a .env file.
    It then sets them as environment variables for the app to use.
    """
    alpha_vantage_key = None
    openai_key = None
    
    try:
        # Try to get from Streamlit secrets first (for deployed apps)
        if hasattr(st, 'secrets') and st.secrets:
            # Check if the specific keys exist in secrets
            try:
                alpha_vantage_key = st.secrets.get("ALPHA_VANTAGE_API_KEY")
                openai_key = st.secrets.get("OPENAI_API_KEY")
                
                if alpha_vantage_key and openai_key:
                    print("✅ Successfully loaded keys from Streamlit Secrets.")
                    return alpha_vantage_key, openai_key
                else:
                    print("⚠️ Secrets exist but keys not found, falling back to .env")
            except Exception as e:
                print(f"⚠️ Error accessing Streamlit secrets: {e}")
    except Exception as e:
        print(f"⚠️ Streamlit secrets not available: {e}")
    
    # Fallback to .env file (for local development)
    print("📁 Loading from .env file...")
    load_dotenv()
    alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if alpha_vantage_key and openai_key:
        print("✅ Successfully loaded keys from .env file.")
        return alpha_vantage_key, openai_key
    else:
        print("❌ Could not load API keys from either source.")
        return None, None

# --- Step 2: Load and Set API Keys ---
try:
    alpha_key, openai_key = load_api_keys()
    
    if alpha_key and openai_key:
        # Set environment variables so the imported class can access them
        os.environ["ALPHA_VANTAGE_API_KEY"] = alpha_key
        os.environ["OPENAI_API_KEY"] = openai_key
        api_keys_loaded = True
    else:
        api_keys_loaded = False
        
except Exception as e:
    st.error(f"Error loading API keys: {e}")
    api_keys_loaded = False

# --- Step 3: Import the News Generator Class ---
try:
    if api_keys_loaded:
        from alpha_news_chill import ProfessionalNewsGenerator
        import_success = True
    else:
        import_success = False
except ImportError as e:
    st.error(f"Could not import ProfessionalNewsGenerator: {e}")
    st.info("Make sure 'alpha_news_chill.py' is in the same directory as this Streamlit app.")
    import_success = False
except Exception as e:
    st.error(f"Error importing class: {e}")
    import_success = False

# --- App Styling ---
st.markdown("""
    <style>
        /* Main button style (blue) */
        .stButton>button {
            border: 2px solid #007bff;
            border-radius: 10px;
            color: white;
            background-color: #007bff;
            padding: 10px 24px;
            text-align: center;
            font-size: 16px;
            font-weight: bold;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #0056b3;
            color: white;
            border-color: #0056b3;
        }
        
        /* Custom style for the 'Clear Results' button (neutral grey) */
        div[data-testid*="stButton"] > button[kind="secondary"] {
            border: 2px solid #6c757d;
            background-color: #6c757d;
            color: white;
        }
        div[data-testid*="stButton"] > button[kind="secondary"]:hover {
            border-color: #5a6268;
            background-color: #5a6268;
            color: white;
        }

        .stTextArea textarea, .stTextInput input {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        .block-container {
            padding-top: 2rem;
        }
        h1, h2, h3 {
            color: #2E4053;
        }
        .status-error {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .status-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'content' not in st.session_state:
    st.session_state.content = None
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False
if 'last_generated_time' not in st.session_state:
    st.session_state.last_generated_time = None

# --- UI Layout ---
st.title("📰 AI-Powered Market News Generator")
st.markdown("Generate professional, multi-format financial news content with a single click. Powered by Alpha Vantage and OpenAI.")

# --- API Key Status Check ---
if not api_keys_loaded:
    st.markdown("""
    <div class="status-error">
        <strong>⚠️ API Keys Not Found</strong><br>
        Please ensure you have either:
        <ul>
            <li><strong>Local Development:</strong> A <code>.env</code> file with your API keys</li>
            <li><strong>Streamlit Cloud:</strong> Secrets configured in your app settings</li>
        </ul>
        Required keys: <code>ALPHA_VANTAGE_API_KEY</code> and <code>OPENAI_API_KEY</code>
    </div>
    """, unsafe_allow_html=True)

if not import_success:
    st.markdown("""
    <div class="status-error">
        <strong>❌ Import Error</strong><br>
        Could not import the ProfessionalNewsGenerator class. Make sure <code>alpha_news_chill.py</code> is in the same directory.
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])

with col1:
    with st.container(border=True):
        st.subheader("Control Panel")
        
        # Status Display
        if not api_keys_loaded or not import_success:
            st.error("❌ System not ready")
            if not api_keys_loaded:
                st.caption("Missing API keys")
            if not import_success:
                st.caption("Import failed")
        elif st.session_state.generation_complete:
            st.success(f"✅ Success! Content generated at: {st.session_state.last_generated_time}")
        else:
            st.info("ℹ️ Status: Ready to generate content.")

        st.divider()

        # Generation Button - disabled if prerequisites not met
        generate_disabled = not (api_keys_loaded and import_success)
        
        if st.button("🚀 Generate Today's Content", disabled=generate_disabled):
            if not generate_disabled:
                with st.spinner('Connecting to APIs and generating content...'):
                    try:
                        generator = ProfessionalNewsGenerator(debug_mode=False)
                        st.session_state.content = generator.generate_content()
                        st.session_state.generation_complete = True
                        st.session_state.last_generated_time = datetime.now().strftime("%H:%M:%S")
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Generation failed: {e}")
                        st.warning("Check your API keys and internet connection.")
                        st.session_state.content = None
                        st.session_state.generation_complete = False

        # Save and Clear buttons
        if st.session_state.generation_complete and st.session_state.content and import_success:
            if st.button("💾 Save to Excel"):
                with st.spinner("Saving data to market_content_tracker.xlsx..."):
                    try:
                        generator = ProfessionalNewsGenerator()
                        filename = generator.save_to_excel(st.session_state.content)
                        st.success(f"Content saved to `{filename}`")
                    except Exception as e:
                        st.error(f"Failed to save to Excel: {e}")
            
            if st.button("🧹 Clear Results", type="secondary"):
                st.session_state.content = None
                st.session_state.generation_complete = False
                st.session_state.last_generated_time = None
                st.rerun()

        # Debug Information (only show in development)
        if st.checkbox("Show Debug Info"):
            st.caption("🔧 Debug Information:")
            st.caption(f"API Keys Loaded: {api_keys_loaded}")
            st.caption(f"Import Success: {import_success}")
            st.caption(f"Alpha Vantage Key: {'✅' if os.getenv('ALPHA_VANTAGE_API_KEY') else '❌'}")
            st.caption(f"OpenAI Key: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")

with col2:
    st.subheader("Generated Content")
    
    if st.session_state.content:
        content = st.session_state.content
        
        # Content Info
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Type", content.get('type', 'N/A'))
        with col_info2:
            st.metric("Day", content.get('day', 'N/A'))
        with col_info3:
            st.metric("Articles", content.get('news_count', 0))
        
        # Content Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎙️ Script", "📱 Social Post", "🎬 Motion Script", "📺 Caption", "🎯 Title"])

        with tab1:
            st.header("Voice Script for Presenter")
            script_text = content.get('script', '')
            st.text_area("Script", value=script_text, height=250, key="script_area")
            if script_text:
                st.caption(f"📝 {len(script_text)} characters | {len(script_text.split())} words")

        with tab2:
            st.header("Social Media Post")
            social_text = content.get('social_post', '')
            st.text_area("Social Post", value=social_text, height=200, key="social_area")
            if social_text:
                st.caption(f"📱 {len(social_text)} characters")

        with tab3:
            st.header("Motion Script (for Presenter)")
            motion_text = content.get('motion_script', '')
            st.text_area("Motion Script", value=motion_text, height=150, key="motion_area")
            if motion_text:
                st.caption(f"🎬 {len(motion_text)} characters")
        
        with tab4:
            st.header("Video Caption")
            st.text_input("Caption", value=content.get('video_caption', ''), key="caption_input")

        with tab5:
            st.header("Episode Title")
            st.text_input("Title", value=content.get('episode_title', ''), key="title_input")
            
    else:
        if api_keys_loaded and import_success:
            st.info("Click the 'Generate Today's Content' button to get started.")
        else:
            st.warning("Please fix the configuration issues above before generating content.")

# --- Footer ---
st.divider()
st.caption("💡 Tip: For local development, create a `.env` file with your API keys. For Streamlit Cloud deployment, use the Secrets management in your app settings.")