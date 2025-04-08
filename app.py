import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from storage import AzureBlobStorage

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ArXiv Paper Summaries",
    description="Daily summaries of recent machine learning papers from arXiv",
    version="1.0.0"
)

# Set up directory for templates and static files
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Create directories if they don't exist
os.makedirs(templates_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

# Initialize templates
templates = Jinja2Templates(directory=templates_dir)

# Serve static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize storage client
storage = AzureBlobStorage()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, date: Optional[str] = None):
    """
    Render the home page with paper summaries for a specific date.
    
    Args:
        request: FastAPI request object
        date: Date in format YYYY-MM-DD, defaults to today
    
    Returns:
        HTML response with rendered template
    """
    # Use today's date if not specified
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Get list of papers for the date
    paper_ids = storage.list_papers_by_date(date)
    
    papers = []
    for paper_id in paper_ids:
        success, summary = storage.get_paper_summary(paper_id, date)
        if success:
            papers.append(summary)
    
    # Sort papers by title
    papers.sort(key=lambda x: x.get("title", ""))
    
    # Generate date options for the date selector (last 7 days)
    date_options = []
    for i in range(7):
        d = datetime.now() - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        date_display = d.strftime("%b %d, %Y")
        date_options.append({
            "value": date_str,
            "display": date_display,
            "selected": date_str == date
        })
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "papers": papers, 
            "date": date,
            "date_options": date_options,
            "paper_count": len(papers)
        }
    )


@app.get("/api/papers")
async def get_papers(date: Optional[str] = None):
    """
    API endpoint to get paper summaries for a specific date.
    
    Args:
        date: Date in format YYYY-MM-DD, defaults to today
    
    Returns:
        JSON response with paper summaries
    """
    # Use today's date if not specified
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Get list of papers for the date
    paper_ids = storage.list_papers_by_date(date)
    
    papers = []
    for paper_id in paper_ids:
        success, summary = storage.get_paper_summary(paper_id, date)
        if success:
            papers.append(summary)
    
    # Sort papers by title
    papers.sort(key=lambda x: x.get("title", ""))
    
    return {"date": date, "papers": papers, "count": len(papers)}


@app.get("/api/paper/{arxiv_id}")
async def get_paper(arxiv_id: str, date: Optional[str] = None):
    """
    API endpoint to get a specific paper summary.
    
    Args:
        arxiv_id: arXiv ID of the paper
        date: Date in format YYYY-MM-DD, defaults to today
    
    Returns:
        JSON response with paper summary
    """
    # Use today's date if not specified
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    success, summary = storage.get_paper_summary(arxiv_id, date)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Paper {arxiv_id} not found")
    
    return summary


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)