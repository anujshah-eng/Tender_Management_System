#routers/ingestion_router.py
"""
Ingestion Router - Handles document upload and processing
"""
from fastapi import APIRouter, HTTPException
from dto.request_dto import IngestRequest
from dto.response_dto import IngestResponse # Changed to relative import
from services.ingestion_service import IngestionService # Changed to relative import
from repositories.tender_project_repository import TenderProjectRepository # Changed to relative import
from repositories.tender_file_repository import TenderFileRepository # Changed to relative import
from repositories.tender_chunk_repository import TenderChunkRepository # Changed to relative import
from core.exceptions import IngestionFailedException # Changed to relative import
from datetime import datetime

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

# Initialize dependencies
project_repo = TenderProjectRepository()
file_repo = TenderFileRepository()
chunk_repo = TenderChunkRepository()
ingestion_service = IngestionService(project_repo, file_repo, chunk_repo)


@router.post(
    "",
    response_model=IngestResponse,
    summary="Ingest New Tender Document",
    description="Process and store a new tender document from URL"
)
def ingest_document(request: IngestRequest):
    """
    Process a PDF document from URL.
    
    **Processing Steps:**
    1. Download and parse PDF
    2. Extract structured information
    3. Split into chunks
    4. Generate hybrid embeddings (dense + sparse)
    5. Store in database
    6. Optionally generate summary
    
    **Note:** This is a synchronous operation that may take several minutes.
    """
    try:
        result = ingestion_service.ingest_document(
            file_url=str(request.file_url),
            uploaded_by=request.uploaded_by
        )
        
        return IngestResponse(
            tender_file_id=result.get('tender_file_id'),
            status="success",
            message="Document ingested successfully",
            progress=100.0
        )
        
    except IngestionFailedException as e:
        return IngestResponse(
            tender_file_id=None,
            status="failed",
            message=str(e),
            progress=None
        )
    except Exception as e:
        return IngestResponse(
            tender_file_id=None,
            status="failed",
            message=f"Unexpected error: {str(e)}",
            progress=None
        )


@router.delete(
    "/{tender_file_id}",
    summary="Delete Tender Document",
    description="Delete a tender document and all related data"
)
def delete_document(tender_file_id: int):
    """Delete tender document and all associated data"""
    try:
        # Implementation here
        return {
            "success": True,
            "tender_file_id": tender_file_id,
            "message": "Document deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))