import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any

import dotenv
from scraper import scrape_arxiv_recent_papers
from pdf_reader import download_and_read_pdf
from summariser import OpenAISummarizer
from storage import AzureBlobStorage

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def process_papers() -> List[Dict[str, Any]]:
    """
    Process the complete pipeline: scrape papers, extract text, summarize, and store.
    
    Returns:
        List of successfully processed paper summaries
    """
    # Initialize components
    logger.info("Initializing components")
    summarizer = OpenAISummarizer()
    storage = AzureBlobStorage()
    
    # Check if components initialized correctly
    if not summarizer.client:
        logger.error("OpenAI summarizer not initialized correctly")
        return []
    
    if not storage.container_client:
        logger.error("Azure Blob Storage not initialized correctly")
        return []
    
    # Scrape papers
    logger.info("Scraping papers from arXiv")
    papers = scrape_arxiv_recent_papers()
    logger.info(f"Found {len(papers)} papers")
    
    successful_summaries = []
    
    # Process each paper
    for i, paper in enumerate(papers):
        logger.info(f"Processing paper {i+1}/{len(papers)}: {paper.title}")
        
        # Check if we already have this paper
        has_paper, _ = storage.get_paper_summary(paper.arxiv_id)
        if has_paper:
            logger.info(f"Paper {paper.arxiv_id} already processed, skipping")
            continue
        
        # Download and read PDF
        logger.info(f"Downloading and reading PDF for {paper.arxiv_id}")
        success, content = download_and_read_pdf(paper.pdf_url)
        
        if not success:
            logger.error(f"Failed to extract text from {paper.arxiv_id}: {content}")
            continue
        
        # Summarize paper
        logger.info(f"Summarizing paper {paper.arxiv_id}")
        summary_success, summary_data = summarizer.summarize_paper(
            title=paper.title,
            authors=paper.authors,
            content=content
        )
        
        if not summary_success:
            logger.error(f"Failed to summarize {paper.arxiv_id}: {summary_data.get('error')}")
            continue
        
        # Save to storage
        logger.info(f"Saving summary for {paper.arxiv_id}")
        storage_success = storage.save_paper_summary(paper.arxiv_id, summary_data)
        
        if storage_success:
            logger.info(f"Successfully processed paper {paper.arxiv_id}")
            successful_summaries.append(summary_data)
        else:
            logger.error(f"Failed to save summary for {paper.arxiv_id}")
    
    logger.info(f"Successfully processed {len(successful_summaries)} out of {len(papers)} papers")
    return successful_summaries


if __name__ == "__main__":
    logger.info("Starting paper processing pipeline")
    
    successful_papers = process_papers()
    
    if successful_papers:
        # Save a local copy of summaries for debugging
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        output_path = os.path.join(output_dir, f"summaries_{today}.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(successful_papers, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved {len(successful_papers)} summaries to {output_path}")
    else:
        logger.warning("No papers were successfully processed")