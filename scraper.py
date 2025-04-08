import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class Paper:
    """Represents an arXiv paper with its metadata."""
    
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    pdf_url: str
    published_date: datetime
    updated_date: Optional[datetime] = None
    categories: List[str] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []


def scrape_arxiv_recent_papers(url: str = "https://arxiv.org/list/cs.LG/recent") -> List[Paper]:
    """
    Scrapes recent papers from arXiv CS.LG category.
    
    Args:
        url: The URL to the arXiv recent papers page. Defaults to CS.LG category.
        
    Returns:
        A list of Paper objects containing metadata about each paper.
        
    Raises:
        requests.RequestException: If there's an issue with the HTTP request.
    """
    logger.info(f"Scraping papers from {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch arXiv page: {e}")
        raise
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract date information
    date_element = soup.select_one("h3")
    if date_element and "New submissions" in date_element.text:
        date_match = re.search(r"for ([a-zA-Z]+, \d+ [a-zA-Z]+ \d{4})", date_element.text)
        if date_match:
            current_date = datetime.strptime(date_match.group(1), "%a, %d %b %Y")
        else:
            current_date = datetime.now()
    else:
        current_date = datetime.now()
    
    papers = []
    # arXiv lists papers in dlpage content
    dl_elements = soup.select("dl")
    
    if not dl_elements:
        logger.warning("No paper listings found on the page")
        return papers
    
    # Usually the first dl element contains the papers
    dl = dl_elements[0]
    
    # Papers alternate between dt (metadata) and dd (content) elements
    dt_elements = dl.select("dt")
    dd_elements = dl.select("dd")
    
    if len(dt_elements) != len(dd_elements):
        logger.warning("Mismatch between paper metadata and content elements")
    
    for i, (dt, dd) in enumerate(zip(dt_elements, dd_elements)):
        try:
            # Extract arXiv ID from the PDF link
            arxiv_id_element = dt.select_one("a[href^='/pdf/']")
            if not arxiv_id_element:
                logger.warning("Could not find PDF link element")
                continue
                
            # Get the ID directly from the href attribute which is more reliable
            pdf_href = arxiv_id_element.get('href', '')
            arxiv_id = pdf_href.replace('/pdf/', '').strip()
            
            if not arxiv_id:
                logger.warning(f"Could not extract valid arXiv ID from href: {pdf_href}")
                continue
            
            # Extract title
            title_element = dd.select_one(".list-title")
            title = title_element.text.replace("Title:", "").strip() if title_element else "Unknown Title"
            
            # Extract authors
            authors_element = dd.select_one(".list-authors")
            if authors_element:
                authors_text = authors_element.text.replace("Authors:", "").strip()
                authors = [author.strip() for author in authors_text.split(",")]
            else:
                authors = []
            
            # Extract abstract
            abstract_element = dd.select_one(".mathjax")
            abstract = abstract_element.text.strip() if abstract_element else ""
            
            # Extract PDF URL using the exact href path
            pdf_url = f"https://arxiv.org{pdf_href}"
            
            # Extract categories
            categories_element = dd.select_one(".list-subjects")
            if categories_element:
                categories_text = categories_element.text.replace("Subjects:", "").strip()
                categories = [cat.strip() for cat in categories_text.split(";")]
            else:
                categories = ["cs.LG"]  # Default to CS.LG
            
            paper = Paper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=abstract,
                pdf_url=pdf_url,
                published_date=current_date,
                categories=categories
            )
            
            papers.append(paper)
            logger.debug(f"Extracted paper: {paper.title}")
            
        except Exception as e:
            logger.error(f"Error processing paper {i}: {e}")
            continue
    
    logger.info(f"Successfully scraped {len(papers)} papers")
    return papers


if __name__ == "__main__":
    # Test the scraper
    papers = scrape_arxiv_recent_papers()
    for i, paper in enumerate(papers[:5], 1):  # Show first 5 papers
        print(f"\nPaper {i}:")
        print(f"Title: {paper.title}")
        print(f"Authors: {', '.join(paper.authors)}")
        print(f"arXiv ID: {paper.arxiv_id}")
        print(f"PDF URL: {paper.pdf_url}")
        print(f"Abstract: {paper.abstract[:150]}...")  # First 150 chars of abstract