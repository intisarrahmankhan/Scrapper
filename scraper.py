import json
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import google.generativeai as genai
from groq import Groq
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtractedField(BaseModel):
    Field_Name: str
    Field_Value: str

def fetch_html_playwright(url: str) -> str:
    """Fetches HTML content using Playwright to handle dynamic JS sites."""
    logger.info(f"Fetching URL with Playwright: {url}")
    with sync_playwright() as p:
        # Launch Chromium headless
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Go to the URL and wait until there are no network connections for at least 500ms
            page.goto(url, wait_until='networkidle', timeout=30000)
            html = page.content()
            return html
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
        finally:
            browser.close()

def clean_html(html_content: str) -> str:
    """Removes scripts, styles, and extracts visible text to save LLM tokens."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remove script, style, meta, and noscript tags
    for element in soup(["script", "style", "meta", "noscript", "header", "footer"]):
        element.extract()
        
    text = soup.get_text(separator="\n")
    
    # Clean up blank lines
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = "\n".join(chunk for chunk in chunks if chunk)
    
    return cleaned_text

def extract_data_with_llm(text: str, instructions: str, api_provider: str, api_key: str) -> list[dict]:
    """Uses the specified LLM provider to extract data into a structured JSON format."""
    system_prompt = (
        "You are an expert web scraping assistant. Your job is to extract data from the provided text based on the user's instructions.\n"
        "You MUST return the data as a JSON array of objects. Each object MUST have exactly two keys: 'Field_Name' and 'Field_Value'.\n"
        "Example Output format:\n"
        "[\n"
        "  {\"Field_Name\": \"Company Name\", \"Field_Value\": \"Example Corp\"},\n"
        "  {\"Field_Name\": \"Price\", \"Field_Value\": \"$100\"}\n"
        "]\n\n"
        "Do NOT include markdown formatting (like ```json), just return the raw JSON array."
    )
    
    user_prompt = f"Instructions: {instructions}\n\nWebsite Text:\n{text[:25000]}" # Limit text to avoid token limits
    
    if api_provider == "Groq":
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="openai/gpt-oss-120b", # Free and very capable replacement model
            temperature=0,
            response_format={"type": "json_object"} # Groq supports JSON mode, but requires the prompt to specify JSON. Our prompt does. But let's handle the array constraint.
        )
        content = response.choices[0].message.content
        
    elif api_provider == "Gemini":
        genai.configure(api_key=api_key)
        # Using gemini-3.5-flash as it has broad availability
        try:
            model = genai.GenerativeModel('gemini-3.5-flash')
            response = model.generate_content(
                f"{system_prompt}\n\n{user_prompt}",
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    max_output_tokens=8192,
                )
            )
        except Exception as e:
            logger.warning(f"Failed with gemini-3.5-flash, falling back to gemini-pro. Error: {e}")
            model = genai.GenerativeModel('gemini-2.5-pro')
            # gemini-pro (1.0) doesn't always strictly support response_mime_type, so we omit it
            response = model.generate_content(
                f"{system_prompt}\n\n{user_prompt}",
                generation_config=genai.GenerationConfig(
                    max_output_tokens=8192,
                )
            )
        
        content = response.text
    else:
        raise ValueError("Invalid API Provider")

    # Clean the response just in case it has markdown code blocks
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    # Try to parse the JSON
    try:
        data = json.loads(content)
        # If the API wrapped the array in an object (e.g. due to JSON object constraint on Groq), unwrap it
        if isinstance(data, dict):
            # Find the first value that is a list
            for key, value in data.items():
                if isinstance(value, list):
                    return value
            return [data] # Fallback
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON. Content: {content}")
        raise ValueError(f"LLM did not return valid JSON. Error: {e}")

def scrape_and_extract(url: str, instructions: str, api_provider: str, api_key: str) -> list[dict]:
    """Main orchestration function."""
    html = fetch_html_playwright(url)
    text = clean_html(html)
    data = extract_data_with_llm(text, instructions, api_provider, api_key)
    return data
