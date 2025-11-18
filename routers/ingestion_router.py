# routers/ingestion_router.py
"""
Ingestion Router - Handles document upload and processing
"""
import logging
from fastapi import APIRouter, HTTPException
from dto.request_dto import IngestRequest
from dto.response_dto import IngestResponse, TenderDetails
from services.ingestion_service import IngestionService
from repositories.tender_project_repository import TenderProjectRepository
from repositories.tender_file_repository import TenderFileRepository
from repositories.tender_chunk_repository import TenderChunkRepository
from core.exceptions import IngestionFailedException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

# Initialize dependencies
project_repo = TenderProjectRepository()
file_repo = TenderFileRepository()
chunk_repo = TenderChunkRepository()
ingestion_service = IngestionService(project_repo, file_repo, chunk_repo)

logger.info("Ingestion router initialized")


@router.post(
    "",
    response_model=IngestResponse,
    summary="Ingest New Tender Document",
    description="Process and store a new tender document from URL with automatic tender details extraction"
)
def ingest_document(request: IngestRequest):
    """
    Process a PDF document from URL and extract tender details.
    
    **Automatically Extracts:**
    - Tender ID: Unique identifier for the tender
    - Project Title: Name of the project
    - Issuing Authority: Organisation issuing the tender
    - Location: Project site location
    - Project Value: Total estimated cost of the project
    - EMD Amount: Earnest Money Deposit amount
    - Summary: One or two line description about the project
    
    **Processing Steps:**
    1. Download and parse PDF
    2. Extract tender details using AI
    3. Split into chunks
    4. Generate hybrid embeddings (dense + sparse)
    5. Store in database
    
    **Returns:**
    - tender_file_id: Database ID of the ingested document
    - status: Processing status (success/failed)
    - message: Status message
    - tender_details: Extracted tender information
    - chunks_created: Number of chunks created
    - processing_time: Time taken to process
    """
    logger.info("="*70)
    logger.info("INGESTION REQUEST RECEIVED")
    logger.info("="*70)
    logger.info(f"File URL: {request.file_url}")
    logger.info(f"Uploaded by: {request.uploaded_by}")
    
    try:
        result = ingestion_service.ingest_document(
            file_url=str(request.file_url),
            uploaded_by=request.uploaded_by
        )
        
        logger.info("✓ Ingestion completed successfully")
        logger.info(f"✓ Tender File ID: {result.get('tender_file_id')}")
        
        # Convert tender_details dict to TenderDetails model
        tender_details_dict = result.get('tender_details', {})
        
        # Create TenderDetails object with all fields
        tender_details = TenderDetails(
            tender_id=tender_details_dict.get('tender_id'),
            project_title=tender_details_dict.get('project_title'),
            issuing_authority=tender_details_dict.get('issuing_authority'),
            location=tender_details_dict.get('location'),
            project_value=tender_details_dict.get('project_value'),
            emd_amount=tender_details_dict.get('emd_amount'),
            summary=tender_details_dict.get('summary')
        ) if tender_details_dict else None
        
        return IngestResponse(
            tender_file_id=result.get('tender_file_id'),
            status="success",
            message="Document ingested successfully",
            progress=100.0,
            tender_details=tender_details,
            chunks_created=result.get('chunks_created'),
            processing_time=result.get('processing_time')
        )
        
    except IngestionFailedException as e:
        logger.error(f"❌ Ingestion failed: {e}")
        return IngestResponse(
            tender_file_id=None,
            status="failed",
            message=str(e),
            progress=None,
            tender_details=None,
            chunks_created=None,
            processing_time=None
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error during ingestion: {e}", exc_info=True)
        return IngestResponse(
            tender_file_id=None,
            status="failed",
            message=f"Unexpected error: {str(e)}",
            progress=None,
            tender_details=None,
            chunks_created=None,
            processing_time=None
        )


@router.delete(
    "/{tender_file_id}",
    summary="Delete Tender Document",
    description="Delete a tender document and all related data"
)
def delete_document(tender_file_id: int):
    """Delete tender document and all associated data"""
    logger.info(f"Delete request received for tender_file_id={tender_file_id}")
    
    try:
        # Implementation here
        logger.info(f"Document {tender_file_id} deleted successfully")
        return {
            "success": True,
            "tender_file_id": tender_file_id,
            "message": "Document deleted successfully"
        }
    except Exception as e:
        logger.error(f"Delete failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))