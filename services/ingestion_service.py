# services/ingestion_service.py
"""
Ingestion Service - Orchestrates document processing
"""
import random
from typing import Dict, Any, Optional
from datetime import datetime
from core.domain_models import TenderProject, TenderFile, TenderChunk # Changed to relative import
from repositories.tender_project_repository import TenderProjectRepository # Changed to relative import
from repositories.tender_file_repository import TenderFileRepository # Changed to relative import
from repositories.tender_chunk_repository import TenderChunkRepository # Changed to relative import
from workflows.ingestion_workflow import ingestion_app # Changed to relative import
from core.exceptions import IngestionFailedException


class IngestionService:
    """Service for document ingestion and processing"""
    
    def __init__(
        self,
        project_repo: TenderProjectRepository,
        file_repo: TenderFileRepository,
        chunk_repo: TenderChunkRepository
    ):
        self.project_repo = project_repo
        self.file_repo = file_repo
        self.chunk_repo = chunk_repo
    
    def ingest_document(
        self, 
        file_url: str,
        uploaded_by: str = "user"
    ) -> Dict[str, Any]:
        """
        Process a new document through the ingestion workflow
        
        Args:
            file_url: URL of the PDF to process
            uploaded_by: User who uploaded the document
            
        Returns:
            Dictionary with processing results
        """
        # Generate unique project ID
        project_id = random.randint(10000, 99999)
        tender_number = f"AUTO-{project_id}"
        
        # Prepare workflow inputs
        inputs = {
            "project_id": project_id,
            "tender_number": tender_number,
            "file_url": file_url,
            "uploaded_by": uploaded_by,
            "tender_date": None,
            "submission_deadline": None,
        }
        
        # Execute workflow
        final_state = ingestion_app.invoke(inputs)
        
        # Check for errors
        if final_state.get('error'):
            raise IngestionFailedException(final_state['error'])
        
        tender_file_id = final_state.get('tender_file_id')
        if not tender_file_id:
            raise IngestionFailedException("Workflow did not return a file ID")
        
        return {
            "tender_file_id": tender_file_id,
            "tender_id": final_state.get('tender_id'),
            "project_id": project_id,
            "chunks_created": len(final_state.get('chunks', [])),
            "status": "success"
        }