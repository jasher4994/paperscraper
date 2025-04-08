import os
import logging
from typing import Dict, List, Optional, Tuple, Any
import json

from openai import AzureOpenAI

import dotenv
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class OpenAISummarizer:
    """Uses Azure OpenAI to generate summaries of academic papers."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment_name: str = "gpt-4o",
        api_version: str = "2023-05-15",
        max_tokens: int = 100000
    ):
        """
        Initialize the OpenAI summarizer.
        
        Args:
            api_key: Azure OpenAI API key, defaults to environment variable AZURE_OPENAI_API_KEY
            endpoint: Azure OpenAI endpoint, defaults to environment variable AZURE_OPENAI_ENDPOINT
            deployment_name: The deployment name to use
            api_version: API version to use
            max_tokens: Maximum tokens in the summary output
        """
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.max_tokens = max_tokens
        
        if not self.api_key or not self.endpoint:
            logger.warning(
                "Azure OpenAI API key or endpoint not provided. "
                "Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables."
            )
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Azure OpenAI client if credentials are available."""
        if self.api_key and self.endpoint:
            try:
                self.client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint
                )
                logger.info("Azure OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {e}")
                self.client = None
    
    def summarize_paper(
        self, 
        title: str, 
        authors: List[str], 
        content: str, 
        max_content_length: int = 8000
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate a summary of an academic paper using Azure OpenAI.
        
        Args:
            title: The title of the paper
            authors: List of authors
            content: The text content of the paper
            max_content_length: Maximum content length to send to OpenAI
            
        Returns:
            A tuple containing (success_flag, summary_data)
            If successful, summary_data contains the structured summary
            If unsuccessful, summary_data contains error information
        """
        if not self.client:
            return False, {"error": "Azure OpenAI client not initialized"}
        
        try:
            # Truncate content if too long
            if len(content) > max_content_length:
                logger.info(f"Truncating content from {len(content)} to {max_content_length} characters")
                content = content[:max_content_length] + "..."
            
            authors_str = ", ".join(authors)
            
            # Create system and user messages
            system_message = """
            You are an AI assistant specialized in summarizing academic machine learning papers.
            Your task is to create a concise, accurate summary highlighting the key contributions,
            methodology, and results. Structure your response in JSON format.
            """
            
            user_message = f"""
            Please summarize the following machine learning paper:
            
            Title: {title}
            Authors: {authors_str}
            
            Content:
            {content}
            
            Format your response as a JSON object with the following fields:
            - "title": Title of the paper
            - "authors": List of authors
            - "summary": A concise summary of the paper (300-500 words)
            - "key_points": A list of 3-5 key takeaways
            - "methodology": Brief description of the methods used
            - "results": Summary of main results
            - "implications": Potential implications or applications
            
            Make sure your response is valid JSON.
            """
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Extract and parse JSON response
            response_text = response.choices[0].message.content
            summary_data = json.loads(response_text)
            
            # Add metadata about the summarization
            summary_data["summarized_by"] = "Azure OpenAI"
            summary_data["model"] = self.deployment_name
            
            logger.info(f"Successfully generated summary for paper: {title}")
            return True, summary_data
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return False, {"error": str(e), "title": title}


if __name__ == "__main__":
    # Test with a sample paper
    from scraper import scrape_arxiv_recent_papers
    from pdf_reader import download_and_read_pdf
    
    # Make sure you've set these environment variables
    # os.environ["AZURE_OPENAI_API_KEY"] = "your-api-key"
    # os.environ["AZURE_OPENAI_ENDPOINT"] = "your-endpoint"
    
    summarizer = OpenAISummarizer()
    
    # Get a sample paper
    papers = scrape_arxiv_recent_papers()
    
    if papers and summarizer.client:
        sample_paper = papers[0]
        print(f"\nTest summarization for paper: {sample_paper.title}")
        
        # Download and read PDF
        success, content = download_and_read_pdf(sample_paper.pdf_url)
        
        if success:
            # Generate summary
            summary_success, summary_data = summarizer.summarize_paper(
                title=sample_paper.title,
                authors=sample_paper.authors,
                content=content
            )
            
            if summary_success:
                print("\nSummary generated successfully:")
                print(json.dumps(summary_data, indent=2))
            else:
                print(f"\nFailed to generate summary: {summary_data.get('error')}")
        else:
            print(f"\nFailed to extract text: {content}")
    else:
        if not papers:
            print("No papers found to test with")
        if not summarizer.client:
            print("Azure OpenAI client not initialized - check your API credentials")