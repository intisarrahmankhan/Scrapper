import streamlit as st
import pandas as pd
import io
import sys
import asyncio
import json
import os
from scraper import scrape_and_extract

# Fix for Playwright asyncio NotImplementedError on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@st.cache_resource(show_spinner=False)
def install_playwright():
    """Ensure Playwright browsers are installed for Streamlit Cloud."""
    if sys.platform.startswith("linux"):
        os.system("playwright install chromium")

install_playwright()

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config_dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_dict, f)

st.set_page_config(
    page_title="AI Web Scraper", 
    page_icon="🕸️", 
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "### AI Web Scraper\n\n**Developer:** Intisar Rahman Khan\n\n*CS Undergrad Student*\n\nThis is a professional AI-powered dynamic web scraping tool designed to extract structured data from any website."
    }
)

# Hide the Deploy button and Stop button, but keep the Main Menu
hide_st_style = """
<style>
.stAppDeployButton {display:none;}
.stStopButton {display:none !important;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("🕸️ AI-Powered Dynamic Web Scraper")
st.markdown("Extract structured data from any website using natural language instructions.")

# Sidebar for Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    config = load_config()
    default_provider = config.get("last_provider", "Gemini")
    
    # Handle index for selectbox
    provider_options = ["Gemini", "Groq"]
    default_index = provider_options.index(default_provider) if default_provider in provider_options else 0
    
    api_provider = st.selectbox(
        "Select AI Provider",
        provider_options,
        index=default_index,
        help="Gemini provides a generous free tier for Gemini 3.5 Flash. Groq provides fast, free access to Llama 3 models."
    )
    
    # Silently update the last used provider so it persists on reload
    if api_provider != config.get("last_provider"):
        config["last_provider"] = api_provider
        save_config(config)
        
    # Automatically grab the correct key for the selected provider
    saved_key = config.get(api_provider, "")
    
    api_key = st.text_input("Enter API Key", value=saved_key, type="password", help=f"Enter your {api_provider} API Key here.")
    
    if api_key == saved_key and api_key != "":
        st.caption("✓ Profile saved")
    elif api_key != saved_key:
        if st.button("📌 Save", use_container_width=False):
            config[api_provider] = api_key
            save_config(config)
            st.rerun()
    
    st.markdown("---")
    st.markdown("""
    **Instructions:**
    1. Enter your chosen API Key (get one from Google AI Studio or Groq Console).
    2. Paste the URL of the website you want to scrape.
    3. Provide clear instructions on what to extract.
    4. Click 'Scrape Data' and download your results.
    """)

# Main Content
col1, col2 = st.columns([1, 1])

with col1:
    url = st.text_input("Website URL", placeholder="https://www.example.com")

with col2:
    instructions = st.text_area(
        "Scraping Instructions", 
        value="Extract all information into a table of two fields. One is 'Field_Name' and another is 'Field_Value'. e.g. Field_Name: Company_Name, Field_Value: Beximco Pharmaceuticals PLC",
        height=100
    )

if st.button("🚀 Scrape Data", type="primary"):
    if not api_key:
        st.error(f"Please enter your {api_provider} API Key in the sidebar.")
    elif not url:
        st.error("Please enter a valid URL.")
    else:
        with st.spinner("Scraping website and extracting data... This may take a minute."):
            try:
                # Run the scraper
                raw_data = scrape_and_extract(url, instructions, api_provider, api_key)
                
                if not raw_data:
                    st.warning("The AI could not find data matching your instructions.")
                else:
                    st.success("Data extracted successfully!")
                    
                    # Convert to pandas DataFrame
                    df = pd.DataFrame(raw_data)
                    
                    # Ensure columns match expectations
                    if 'Field_Name' not in df.columns or 'Field_Value' not in df.columns:
                        st.warning("The AI did not perfectly follow the Field_Name/Field_Value schema, but here is the data:")
                    
                    st.dataframe(df, use_container_width=True)
                    
                    st.markdown("### 📥 Download Results")
                    col_dl1, col_dl2 = st.columns(2)
                    
                    # CSV Download
                    csv = df.to_csv(index=False).encode('utf-8')
                    with col_dl1:
                        st.download_button(
                            label="Download as CSV",
                            data=csv,
                            file_name='scraped_data.csv',
                            mime='text/csv',
                        )
                        
                    # Excel Download
                    # Write to BytesIO buffer
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Data')
                    
                    with col_dl2:
                        st.download_button(
                            label="Download as Excel (XLSX)",
                            data=buffer.getvalue(),
                            file_name='scraped_data.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        )
                        
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)
