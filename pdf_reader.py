import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import fitz  # PyMuPDF
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def download_and_read_pdf(url: str, timeout: int = 30) -> Tuple[bool, Optional[str]]:
    """
    Downloads a PDF from a URL and extracts its text content.
    
    Args:
        url: URL to the PDF file
        timeout: Request timeout in seconds
        
    Returns:
        A tuple containing (success_flag, text_content)
        If successful, success_flag is True and text_content contains the PDF text
        If unsuccessful, success_flag is False and text_content contains error information
    """
    logger.info(f"Downloading PDF from {url}")
    
    try:
        # Download the PDF
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download PDF: {e}")
        return False, f"Download error: {str(e)}"
    
    # Create a temporary file to save the PDF
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        logger.info(f"PDF downloaded to temporary file: {tmp_path}")
        
        # Extract text from PDF using PyMuPDF
        return extract_text_from_pdf(tmp_path)
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        return False, f"PDF processing error: {str(e)}"
    
    finally:
        # Clean up the temporary file
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
                logger.debug(f"Deleted temporary file: {tmp_path}")
        except Exception as e:
            logger.warning(f"Failed to delete temporary file: {e}")


def extract_text_from_pdf(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Extracts text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        A tuple containing (success_flag, text_content)
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    
    try:
        # Open the PDF file
        pdf_document = fitz.open(file_path)
        
        # Extract text from each page
        text_content = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text_content += page.get_text()
        
        # Close the document
        pdf_document.close()
        
        if not text_content.strip():
            logger.warning("Extracted empty text from PDF")
            return False, "PDF contains no extractable text"
        
        logger.info(f"Successfully extracted {len(text_content)} characters from PDF")
        return True, text_content
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return False, f"Text extraction error: {str(e)}"


if __name__ == "__main__":
    # Import the scraper to test with a real paper
    from scraper import scrape_arxiv_recent_papers
    
    # Get a sample paper
    papers = scrape_arxiv_recent_papers()
    
    if papers:
        sample_paper = papers[0]
        print(f"\nTesting PDF extraction for paper: {sample_paper.title}")
        print(f"PDF URL: {sample_paper.pdf_url}")
        
        success, content = download_and_read_pdf(sample_paper.pdf_url)
        
        if success:
            # Print the first 500 characters of the content
            print("\nExtracted text (first 500 chars):")
            print(content[:500] + "...")
            print(f"\nTotal text length: {len(content)} characters")
        else:
            print(f"\nFailed to extract text: {content}")
    else:
        print("No papers found to test with")