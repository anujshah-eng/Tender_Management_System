"""
Ingestion Service - Orchestrates document processing
"""
import random
import logging
import time
from typing import Dict, Any
from core.domain_models import TenderProject, TenderFile, TenderChunk
from repositories.tender_project_repository import TenderProjectRepository
from repositories.tender_file_repository import TenderFileRepository
from repositories.tender_chunk_repository import TenderChunkRepository
from workflows.ingestion_workflow import ingestion_app
from core.exceptions import IngestionFailedException

logger = logging.getLogger(__name__)


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
        logger.info("IngestionService initialized")
    
    def ingest_document(
        self, 
        file_url: str,
        uploaded_by: str = "user"
    ) -> Dict[str, Any]:
        """
        Process a new document through the ingestion workflow
        """
        start_time = time.time()
        
        logger.info("="*70)
        logger.info("STARTING DOCUMENT INGESTION")
        logger.info("="*70)
        logger.info(f"File URL: {file_url}")
        logger.info(f"Uploaded by: {uploaded_by}")
        
        # Generate unique project ID
        project_id = random.randint(10000, 99999)
        tender_number = f"AUTO-{project_id}"
        
        logger.debug(f"Generated project_id: {project_id}")
        logger.debug(f"Generated tender_number: {tender_number}")
        
        # Prepare workflow inputs
        inputs = {
            "project_id": project_id,
            "tender_number": tender_number,
            "file_url": file_url,
            "uploaded_by": uploaded_by,
            "tender_date": None,
            "submission_deadline": None,
        }
        
        logger.info("Executing ingestion workflow...")
        
        try:
            # Execute workflow
            final_state = ingestion_app.invoke(inputs)
            
            # Check for errors
            if final_state.get('error'):
                logger.error(f"Ingestion failed: {final_state['error']}")
                raise IngestionFailedException(final_state['error'])
            
            tender_file_id = final_state.get('tender_file_id')
            if not tender_file_id:
                logger.error("Workflow did not return a file ID")
                raise IngestionFailedException("Workflow did not return a file ID")
            
            chunks_created = len(final_state.get('chunks', []))
            processing_time = time.time() - start_time
            
            # Get extracted tender details (these are for display)
            tender_details = final_state.get('extracted_tender_details', {})
            
            # Ensure all fields are present
            tender_details_response = {
                "tender_id": tender_details.get('tender_id'),
                "project_title": tender_details.get('project_title'),
                "issuing_authority": tender_details.get('issuing_authority'),
                "location": tender_details.get('location'),
                "project_value": tender_details.get('project_value'),
                "emd_amount": tender_details.get('emd_amount'),
                "summary": tender_details.get('summary')
            }
            
            logger.info("="*70)
            logger.info("INGESTION COMPLETED SUCCESSFULLY")
            logger.info("="*70)
            logger.info(f"✓ Tender File ID: {tender_file_id}")
            logger.info(f"✓ Tender ID: {final_state.get('tender_id')}")
            logger.info(f"✓ Project Title: {tender_details_response.get('project_title', 'N/A')}")
            logger.info(f"✓ Issuing Authority: {tender_details_response.get('issuing_authority', 'N/A')}")
            logger.info(f"✓ Location: {tender_details_response.get('location', 'N/A')}")
            logger.info(f"✓ Project Value: {tender_details_response.get('project_value', 'N/A')}")
            logger.info(f"✓ EMD Amount: {tender_details_response.get('emd_amount', 'N/A')}")
            logger.info(f"✓ Chunks Created: {chunks_created}")
            logger.info(f"✓ Processing Time: {processing_time:.2f}s")
            logger.info("="*70)
            
            return {
                "tender_file_id": tender_file_id,
                "tender_id": final_state.get('tender_id'),
                "project_id": project_id,
                "chunks_created": chunks_created,
                "processing_time": processing_time,
                "tender_details": tender_details_response,
                "status": "success"
            }
            
        except IngestionFailedException as e:
            # Re-raise ingestion failures
            raise
        except Exception as e:
            logger.error(f"Unexpected error during ingestion: {e}", exc_info=True)
            raise IngestionFailedException(f"Unexpected error: {str(e)}")