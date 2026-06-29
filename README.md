# AI-Powered Dynamic Web Scraper

An intelligent, natural language-driven web scraper developed by **Intisar Rahman Khan**, CS Undergrad Student.

## 🚀 Usability
Traditional web scraping scripts break easily when a website updates its layout or HTML classes. This project solves that problem. By leveraging powerful Large Language Models (LLMs), this tool can read the raw text of any website and intelligently extract the data you want simply by providing plain English instructions. 

It is highly adaptable, requires zero coding to scrape new sites, and outputs the scraped data into structured, downloadable CSV and Excel files.

## 💻 Technology Used
- **Streamlit:** Serves as the interactive, production-ready frontend framework.
- **Playwright:** Automates headless Chromium browsers to fetch dynamic, JavaScript-rendered websites.
- **BeautifulSoup 4:** Cleans and parses raw HTML to reduce token usage and format it for the AI.
- **Google Gemini & Groq APIs:** State-of-the-art LLMs (like Gemini 3.5 Flash and Llama) that process the website text and intelligently map it to a structured JSON schema.
- **Pandas:** Transforms the AI's JSON output into structural DataFrames for CSV/Excel exporting.

## ⚙️ How it Works
1. **Fetch:** Playwright launches a hidden browser, navigates to your target URL, waits for the network to idle (ensuring all JavaScript loads), and extracts the raw HTML.
2. **Clean:** BeautifulSoup strips out unnecessary tags (like `<script>`, `<style>`, `<nav>`) to compress the data, making it token-efficient for the AI.
3. **Analyze & Extract:** The cleaned text and your natural language instructions are sent to the chosen AI provider (Gemini or Groq). The AI reads the page like a human would and constructs a precise JSON array containing your target data.
4. **Format:** The application parses the returned JSON, converts it into a Pandas DataFrame, and displays it in an interactive table with immediate download options.

---

## Setup Instructions

### Prerequisites
- Python 3.9 or higher

### 1. Create a virtual environment (Recommended)
Open your terminal in the project directory and run:
```bash
python -m venv venv
```

### 2. Activate the virtual environment
- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
This app uses Playwright to extract data from websites. You must install the browser binaries:
```bash
playwright install chromium
```

### 5. Running the App
Once setup is complete, you can start the application by running:
```bash
streamlit run app.py
```
This will automatically open the web application in your default web browser.
