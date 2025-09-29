import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", message="No secrets found")

# --- Page Configuration ---
st.set_page_config(
    page_title="Market News Content Generator",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Load API Keys ---
def load_api_keys():
    """Load API keys from Streamlit secrets or .env file"""
    alpha_vantage_key = None
    openai_key = None
    
    try:
        # Try Streamlit secrets first (for deployed apps)
        if hasattr(st, 'secrets') and st.secrets:
            try:
                alpha_vantage_key = st.secrets.get("ALPHA_VANTAGE_API_KEY")
                openai_key = st.secrets.get("OPENAI_API_KEY")
                
                if alpha_vantage_key and openai_key:
                    return alpha_vantage_key, openai_key
            except Exception:
                pass
    except Exception:
        pass
    
    # Fallback to .env file (for local development)
    load_dotenv()
    alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    return alpha_vantage_key, openai_key

# --- Load and Set API Keys ---
try:
    alpha_key, openai_key = load_api_keys()
    
    if alpha_key and openai_key:
        os.environ["ALPHA_VANTAGE_API_KEY"] = alpha_key
        os.environ["OPENAI_API_KEY"] = openai_key
        api_keys_loaded = True
    else:
        api_keys_loaded = False
        
except Exception as e:
    st.error(f"Error loading API keys: {e}")
    api_keys_loaded = False

# --- Helper Functions ---
def _display_headlines():
    """Display headlines in Streamlit format"""
    headlines = st.session_state.headlines
    
    if not headlines:
        st.info("No headlines available")
        return
    
    st.caption(f"Found {len(headlines)} major headlines (🥇 Gold | ₿ Bitcoin/Crypto | 📅 Previous days)")
    
    for i, headline in enumerate(headlines, 1):
        # Format timestamp and age
        time_pub = headline.get('time_published', '')
        age_indicator = ""
        formatted_time = "Recent"
        
        if time_pub and len(time_pub) >= 8:
            try:
                pub_date = datetime.strptime(time_pub[:8], '%Y%m%d')
                today = datetime.now().date()
                days_ago = (today - pub_date.date()).days
                
                if days_ago == 0:
                    formatted_time = f"{time_pub[4:6]}/{time_pub[6:8]} {time_pub[9:11]}:{time_pub[11:13]}"
                elif days_ago == 1:
                    formatted_time = f"Yesterday {time_pub[9:11]}:{time_pub[11:13]}"
                    age_indicator = " 📅"
                elif days_ago <= 7:
                    formatted_time = f"{days_ago}d ago {time_pub[9:11]}:{time_pub[11:13]}"
                    age_indicator = " 📅"
            except:
                pass
        
        # Format tickers
        tickers_display = ""
        if headline.get('tickers'):
            tickers_display = f" [{', '.join(headline['tickers'][:3])}]"
        
        # Determine icon with proper gold filtering
        title_lower = headline.get('title', '').lower()
        summary_lower = headline.get('summary', '').lower()
        
        # Check for actual gold (not Goldman Sachs)
        is_gold_news = False
        if 'gold' in title_lower or 'gold' in summary_lower:
            goldman_terms = ['goldman sachs', 'goldman', 'gs group']
            if not any(term in title_lower or term in summary_lower for term in goldman_terms):
                is_gold_news = True

        if is_gold_news:
            icon = "🥇"
        elif any(term in title_lower or term in summary_lower for term in ['bitcoin', 'btc', 'crypto', 'ethereum']):
            icon = "₿"
        elif headline.get('sentiment') == 'bullish':
            icon = "📈"
        elif headline.get('sentiment') == 'bearish':
            icon = "📉"
        else:
            icon = "📊"
        
        # Display headline
        with st.container():
            st.markdown(f"""
            <div class="headline-item">
                <div class="headline-title">{i:2d}. {headline['title']}{tickers_display}{age_indicator}</div>
                <div class="headline-meta">{icon} {headline.get('sentiment', 'neutral').title()} | {headline.get('source', 'Unknown')} | {formatted_time}</div>
                <div class="headline-summary">{headline.get('summary', '')[:150]}{'...' if len(headline.get('summary', '')) > 150 else ''}</div>
            </div>
            """, unsafe_allow_html=True)


# --- Import the News Generator Class ---
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
        .headline-item {
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
        }
        .headline-title {
            font-weight: bold;
            color: #2E4053;
            margin-bottom: 5px;
        }
        .headline-meta {
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 5px;
        }
        .headline-summary {
            font-size: 0.95em;
            color: #495057;
        }
        .style-selector {
            background-color: #f0f8ff;
            border: 1px solid #007bff;
            border-radius: 8px;
            padding: 10px;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'content' not in st.session_state:
    st.session_state.content = None
if 'headlines' not in st.session_state:
    st.session_state.headlines = None
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False
if 'headlines_loaded' not in st.session_state:
    st.session_state.headlines_loaded = False
if 'last_generated_time' not in st.session_state:
    st.session_state.last_generated_time = None
if 'selected_style' not in st.session_state:
    st.session_state.selected_style = 'classic_daily'

# --- UI Layout ---
st.title("📰 AI-Powered Market News Generator")
st.markdown("Generate professional, multi-format financial news content with **5 distinct presentation styles**.")

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

# --- Main Layout ---
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
            st.success(f"✅ Content generated at: {st.session_state.last_generated_time}")
            if st.session_state.content and 'style' in st.session_state.content:
                st.info(f"🎨 Style: {st.session_state.content['style']}")
        elif st.session_state.headlines_loaded:
            st.success("✅ Headlines loaded")
        else:
            st.info("ℹ️ Ready to generate content")

        st.divider()

        # Style Selection Section
        if api_keys_loaded and import_success:
            st.markdown('<div class="style-selector">', unsafe_allow_html=True)
            st.subheader("🎨 Content Style")
            
            try:
                generator = ProfessionalNewsGenerator()
                available_styles = generator.get_available_styles()
                
                style_options = {}
                for key, info in available_styles.items():
                    style_options[f"{info['name']} ({info['target_seconds']}s)"] = key
                
                selected_display = st.selectbox(
                    "Choose presentation style:",
                    options=list(style_options.keys()),
                    index=0,
                    help="Each style has a distinct tone, pacing, and structure"
                )
                
                # Update session state with selected style
                st.session_state.selected_style = style_options[selected_display]
                
                # Show style description
                selected_info = available_styles[st.session_state.selected_style]
                st.caption(f"📝 {selected_info['description']}")
                
            except Exception as e:
                st.error(f"Error loading styles: {e}")
                st.session_state.selected_style = 'classic_daily'
            
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        # Generation Buttons
        generate_disabled = not (api_keys_loaded and import_success)
        
        if st.button("🚀 Generate Today's Content", disabled=generate_disabled):
            if not generate_disabled:
                with st.spinner(f'Generating content in {available_styles[st.session_state.selected_style]["name"]} style...'):
                    try:
                        generator = ProfessionalNewsGenerator(debug_mode=False)
                        st.session_state.content = generator.generate_content(style_key=st.session_state.selected_style)
                        st.session_state.generation_complete = True
                        st.session_state.last_generated_time = datetime.now().strftime("%H:%M:%S")
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Generation failed: {e}")
                        st.session_state.content = None
                        st.session_state.generation_complete = False

        if st.button("📰 View Major Headlines", disabled=generate_disabled):
            if not generate_disabled:
                with st.spinner('Fetching major headlines...'):
                    try:
                        generator = ProfessionalNewsGenerator(debug_mode=False)
                        headlines = generator.get_major_headlines()
                        st.session_state.headlines = headlines
                        st.session_state.headlines_loaded = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to fetch headlines: {e}")
                        st.session_state.headlines = None
                        st.session_state.headlines_loaded = False

        if st.button("🎯 Generate Content + Headlines", disabled=generate_disabled):
            if not generate_disabled:
                with st.spinner(f'Generating content and headlines in {available_styles[st.session_state.selected_style]["name"]} style...'):
                    try:
                        generator = ProfessionalNewsGenerator(debug_mode=False)
                        st.session_state.content = generator.generate_content(style_key=st.session_state.selected_style)
                        st.session_state.headlines = generator.get_major_headlines()
                        st.session_state.generation_complete = True
                        st.session_state.headlines_loaded = True
                        st.session_state.last_generated_time = datetime.now().strftime("%H:%M:%S")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Generation failed: {e}")
                        st.session_state.content = None
                        st.session_state.headlines = None
                        st.session_state.generation_complete = False
                        st.session_state.headlines_loaded = False

        # Action Buttons
        if (st.session_state.generation_complete and st.session_state.content and import_success):
            if st.button("💾 Save to Excel"):
                with st.spinner("Saving to Excel..."):
                    try:
                        generator = ProfessionalNewsGenerator()
                        filename = generator.save_to_excel(st.session_state.content)
                        st.success(f"Content saved to `{filename}`")
                        st.info("Excel file includes Major_Headlines tab with Gold/Bitcoin coverage")
                        if 'style' in st.session_state.content:
                            st.info(f"Style information saved: {st.session_state.content['style']}")
                    except Exception as e:
                        st.error(f"Failed to save: {e}")
            
        if st.button("🧹 Clear Results", type="secondary"):
            st.session_state.content = None
            st.session_state.headlines = None
            st.session_state.generation_complete = False
            st.session_state.headlines_loaded = False
            st.session_state.last_generated_time = None
            st.rerun()

# --- Display Results ---
with col2:
    if st.session_state.content and st.session_state.headlines:
        # Both content and headlines
        tab1, tab2 = st.tabs(["📺 Generated Content", "📰 Major Headlines"])
        
        with tab1:
            content = st.session_state.content
            
            # Content Info with Style
            col_info1, col_info2, col_info3, col_info4 = st.columns(4)
            with col_info1:
                st.metric("Type", content.get('type', 'N/A'))
            with col_info2:
                st.metric("Day", content.get('day', 'N/A'))
            with col_info3:
                st.metric("Articles", content.get('news_count', 0))
            with col_info4:
                st.metric("Style", content.get('style', 'Classic Daily Brief'))
            
            # Content Tabs
            subtab1, subtab2, subtab3, subtab4, subtab5 = st.tabs(["🎙️ Script", "📱 Social", "🎬 Motion", "📺 Caption", "🎯 Title"])

            with subtab1:
                script_text = content.get('script', '')
                st.text_area("Voice Script for Presenter", value=script_text, height=250, key="script_area")
                if script_text:
                    st.caption(f"📝 {len(script_text)} characters | {len(script_text.split())} words | Style: {content.get('style', 'N/A')}")

            with subtab2:
                social_text = content.get('social_post', '')
                st.text_area("Social Media Post", value=social_text, height=200, key="social_area")
                if social_text:
                    st.caption(f"📱 {len(social_text)} characters")

            with subtab3:
                motion_text = content.get('motion_script', '')
                st.text_area("Motion Script (for Presenter)", value=motion_text, height=150, key="motion_area")

            with subtab4:
                st.text_input("Video Caption", value=content.get('video_caption', ''), key="caption_input")

            with subtab5:
                st.text_input("Episode Title", value=content.get('episode_title', ''), key="title_input")
        
        with tab2:
            st.subheader("📰 Major Market Headlines")
            _display_headlines()
    
    elif st.session_state.content:
        # Content only
        st.subheader("📺 Generated Content")
        content = st.session_state.content
        
        # Content Info with Style
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        with col_info1:
            st.metric("Type", content.get('type', 'N/A'))
        with col_info2:
            st.metric("Day", content.get('day', 'N/A'))
        with col_info3:
            st.metric("Articles", content.get('news_count', 0))
        with col_info4:
            st.metric("Style", content.get('style', 'Classic Daily Brief'))
        
        st.info("ℹ️ The script below is generated from the most recent news. For a broader high impact news view, please see the 'Major Headlines' tab.")
        
        # Content Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎙️ Script", "📱 Social", "🎬 Motion", "📺 Caption", "🎯 Title"])

        with tab1:
            script_text = content.get('script', '')
            st.text_area("Voice Script for Presenter", value=script_text, height=250, key="script_area")
            if script_text:
                st.caption(f"📝 {len(script_text)} characters | {len(script_text.split())} words | Style: {content.get('style', 'N/A')}")

        with tab2:
            social_text = content.get('social_post', '')
            st.text_area("Social Media Post", value=social_text, height=200, key="social_area")
            if social_text:
                st.caption(f"📱 {len(social_text)} characters")

        with tab3:
            motion_text = content.get('motion_script', '')
            st.text_area("Motion Script (for Presenter)", value=motion_text, height=150, key="motion_area")

        with tab4:
            st.text_input("Video Caption", value=content.get('video_caption', ''), key="caption_input")

        with tab5:
            st.text_input("Episode Title", value=content.get('episode_title', ''), key="title_input")
    
    elif st.session_state.headlines:
        # Headlines only
        st.subheader("📰 Major Market Headlines")
        _display_headlines()
    
    else:
        # No content loaded
        if api_keys_loaded and import_success:
            st.info("Choose an option from the Control Panel to get started:")
            st.markdown("""
            - **🚀 Generate Today's Content**: Create professional scripts in your selected style
            - **📰 View Major Headlines**: See today's major market news with Gold/Bitcoin coverage  
            - **🎯 Generate Content + Headlines**: Get both content and headlines together
            
            **🎨 Style Selection**: Choose from 5 distinct presentation styles:
            - **Classic Daily Brief**: Professional, conversational daily updates
            - **Breaking News Alert**: Urgent, dramatic market developments
            - **Weekly Deep Dive**: Analytical, comprehensive analysis  
            - **Market Pulse**: Energetic, rhythm-focused updates
            - **Strategic Outlook**: Advisory, institutional positioning
            """)
        else:
            st.warning("Please fix the configuration issues shown above before generating content.")

# --- Footer ---
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption("💡 Tip: This app guarantees Gold and Bitcoin coverage in headlines, even from previous days if today's news is quiet.")
with col2:
    st.caption("🎨 New: 5 distinct content styles for different presentation needs - select your style in the Control Panel!")


