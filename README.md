# DailyMachineLearning.com: ML Paper Summarizer

A web application that provides daily summaries of machine learning research papers from arXiv, powered by Azure OpenAI.


## 🔗 [Visit dailymachinelearning.com](https://dailymachinelearning.com)

#### By [James Asher](https://www.linkedin.com/in/james-alexander-asher/)

## 📋 Overview

This project automatically scrapes recent ML papers from arXiv, uses Azure OpenAI to create concise summaries, and presents them in a clean, searchable web interface. New papers are processed every 8 hours and organized by date for easy browsing.


### Paper Scraper (GitHub Actions)

* **Schedule**: Runs every 8 hours via GitHub Actions workflow
* **Process**:
  1. Scrapes the latest ML papers from arXiv
  2. Downloads and processes the PDFs
  3. Generates summaries using Azure OpenAI
  4. Organizes the summaries by date
  5. Saves them to Azure Blob Storage

* **Key files**:
  * `main.py` - Main processing script
  * `scraper.py` - Extracts paper metadata from arXiv
  * `pdf_reader.py` - Downloads and extracts text from PDFs
  * `summariser.py` - Generates summaries with Azure OpenAI
  * `storage.py` - Handles saving to Azure Blob Storage

* **Storage structure**:
  * Summaries are stored in a hierarchical structure by date
  * Path format: `YYYY-MM-DD/{arxiv_id}.json`

### Web Interface (Azure App Service)

* **Availability**: Always on, serving requests
* **Process**:
  1. On page load, checks what date is requested (default: today)
  2. Lists all blob files from that date's directory in storage
  3. Loads the JSON data for each paper summary
  4. Renders them using the HTML template

* **Key files**:
  * `app.py` - FastAPI web application
  * `templates/index.html` - Frontend user interface
  * `storage.py` - Shared code for accessing Azure Blob Storage

### How Daily Reloading Works

When a user visits the site:
1. The FastAPI application checks the requested date (defaulting to today)
2. It queries Azure Blob Storage for all papers from that date
3. The storage service returns the papers organized in a date-based structure
4. The app displays the summaries in a responsive grid layout

When new papers are added:
1. GitHub Actions runs the scraper script every 8 hours
2. New papers are processed and saved to the current date's folder
3. The next time a user visits, they'll see the newly added papers

## 🛠️ Technologies Used

- **Backend**: Python with FastAPI
- **Frontend**: HTML, CSS, Bootstrap 5
- **AI**: Azure OpenAI (GPT-4)
- **Storage**: Azure Blob Storage
- **CI/CD**: GitHub Actions
- **Hosting**: Azure App Service

## 📜 arXiv Policy Compliance

This project complies with arXiv's policies on appropriate use of their content. According to arXiv's website, the following activities are explicitly encouraged:

### "Things that you can (and should!) do"

- **Retrieve, store, transform, and share descriptive metadata about arXiv e-prints.**
  - Our app retrieves and transforms metadata to make papers more discoverable.

- **Retrieve, store, and use the content of arXiv e-prints for your own personal use, or for research purposes.**
  - We retrieve paper content solely for the purpose of generating research-focused summaries.

- **Provide tools and services to users that helps them to discover or be notified about arXiv e-prints. For example:**
  - **A better search interface**
    - Our app provides a clean, modern interface for browsing recent ML papers.
  - **A mobile app that notifies users about e-prints that might be of interest to them**
    - While we don't currently have notifications, our daily summaries help users quickly identify papers of interest.

This application is designed to enhance arXiv's mission of making research more accessible by providing concise summaries that help researchers decide which papers to read in full on arXiv.

For more information, see arXiv's [Terms of Use](https://arxiv.org/help/api/tou).


## 🚀 Deployment

### GitHub Actions for Paper Processing

The GitHub Actions workflow automatically runs every 8 hours to process new papers:

1. **Workflow Configuration** (.github/workflows/paper-scraper.yml):
```yaml
name: Run Paper Scraper

on:
  schedule:
    - cron: '0 0,8,16 * * *'  # Run every 8 hours
  workflow_dispatch:  # Allow manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: Run paper scraper
      env:
        AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
        AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
        AZURE_STORAGE_CONNECTION_STRING: ${{ secrets.AZURE_STORAGE_CONNECTION_STRING }}
      run: python main.py
