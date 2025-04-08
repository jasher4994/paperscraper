import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

import dotenv
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AzureBlobStorage:
    """Handles storage operations with Azure Blob Storage."""
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        container_name: str = "paper-summaries"
    ):
        """
        Initialize the Azure Blob Storage client.
        
        Args:
            connection_string: Azure Storage connection string, defaults to environment variable
            container_name: Name of the blob container to use
        """
        self.connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = container_name
        
        if not self.connection_string:
            logger.warning(
                "Azure Storage connection string not provided. "
                "Set AZURE_STORAGE_CONNECTION_STRING environment variable."
            )
        
        self.blob_service_client = None
        self.container_client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Azure Blob Storage client and ensure container exists."""
        if not self.connection_string:
            return
        
        try:
            # Initialize the blob service client
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            logger.info("Azure Blob Storage client initialized successfully")
            
            # Create container if it doesn't exist
            try:
                self.container_client = self.blob_service_client.create_container(self.container_name)
                logger.info(f"Container '{self.container_name}' created successfully")
            except ResourceExistsError:
                self.container_client = self.blob_service_client.get_container_client(self.container_name)
                logger.info(f"Using existing container '{self.container_name}'")
                
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage: {e}")
            self.blob_service_client = None
            self.container_client = None
    
    def save_paper_summary(self, arxiv_id: str, summary_data: Dict[str, Any]) -> bool:
        """
        Save a paper summary to Azure Blob Storage.
        
        Args:
            arxiv_id: The arXiv ID of the paper
            summary_data: Dictionary containing the paper summary data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.container_client:
            logger.error("Azure Blob Storage not initialized")
            return False
        
        try:
            # Create a blob name based on arXiv ID and current date
            today = datetime.now().strftime("%Y-%m-%d")
            blob_name = f"{today}/{arxiv_id}.json"
            
            # Add metadata about when it was saved
            summary_data["stored_date"] = today
            summary_data["arxiv_id"] = arxiv_id
            
            # Convert to JSON
            json_data = json.dumps(summary_data, ensure_ascii=False, indent=2)
            
            # Upload to blob storage
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.upload_blob(json_data, overwrite=True)
            
            logger.info(f"Successfully saved summary for paper {arxiv_id} to {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save paper summary for {arxiv_id}: {e}")
            return False
    
    def get_paper_summary(self, arxiv_id: str, date: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Retrieve a paper summary from Azure Blob Storage.
        
        Args:
            arxiv_id: The arXiv ID of the paper
            date: Optional date string in format YYYY-MM-DD, defaults to today
            
        Returns:
            A tuple containing (success_flag, summary_data)
        """
        if not self.container_client:
            logger.error("Azure Blob Storage not initialized")
            return False, None
        
        try:
            # Determine blob name
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            blob_name = f"{date}/{arxiv_id}.json"
            
            # Get blob client
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Download data
            download_stream = blob_client.download_blob()
            json_data = download_stream.readall()
            
            # Parse JSON
            summary_data = json.loads(json_data)
            
            logger.info(f"Successfully retrieved summary for paper {arxiv_id}")
            return True, summary_data
            
        except ResourceNotFoundError:
            logger.warning(f"Summary for paper {arxiv_id} not found")
            return False, None
        except Exception as e:
            logger.error(f"Failed to retrieve paper summary for {arxiv_id}: {e}")
            return False, None
    
    def list_papers_by_date(self, date: Optional[str] = None) -> List[str]:
        """
        List all paper IDs available for a specific date.
        
        Args:
            date: Date string in format YYYY-MM-DD, defaults to today
            
        Returns:
            List of arXiv IDs
        """
        if not self.container_client:
            logger.error("Azure Blob Storage not initialized")
            return []
        
        try:
            # Determine prefix
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            prefix = f"{date}/"
            
            # List blobs with the prefix
            blobs = self.container_client.list_blobs(name_starts_with=prefix)
            
            # Extract arXiv IDs from blob names
            arxiv_ids = []
            for blob in blobs:
                # Blob name format is date/arxiv_id.json
                filename = blob.name.split('/')[-1]
                arxiv_id = filename.replace('.json', '')
                arxiv_ids.append(arxiv_id)
            
            return arxiv_ids
            
        except Exception as e:
            logger.error(f"Failed to list papers for date {date}: {e}")
            return []


if __name__ == "__main__":
    # Test the storage module
    storage = AzureBlobStorage()
    
    if storage.container_client:
        # Create a test summary
        test_summary = {
            "title": "Test Paper",
            "authors": ["Author One", "Author Two"],
            "summary": "This is a test summary of a paper.",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "methodology": "Test methodology",
            "results": "Test results",
            "implications": "Test implications"
        }
        
        # Save the test summary
        test_arxiv_id = "test.12345"
        success = storage.save_paper_summary(test_arxiv_id, test_summary)
        
        if success:
            print(f"Successfully saved test summary for {test_arxiv_id}")
            
            # Retrieve the summary
            get_success, retrieved_summary = storage.get_paper_summary(test_arxiv_id)
            
            if get_success:
                print("Retrieved summary successfully:")
                print(json.dumps(retrieved_summary, indent=2))
            else:
                print("Failed to retrieve the test summary")
                
            # List papers for today
            today = datetime.now().strftime("%Y-%m-%d")
            paper_ids = storage.list_papers_by_date(today)
            
            print(f"\nPapers available for {today}:")
            for paper_id in paper_ids:
                print(f"- {paper_id}")
        else:
            print("Failed to save test summary")
    else:
        print("Azure Blob Storage not initialized - check your connection string")