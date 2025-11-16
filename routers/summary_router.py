# routers/summary_router.py
"""
Summary Router with SSE Streaming Support
"""
from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import StreamingResponse
from dto.request_dto import SummaryRequest
from dto.response_dto import SummaryResponse
from services.streaming_service import StreamingService
from services.retrieval_service import RetrievalService
from services.embedding_service import EmbeddingService
from repositories.tender_chunk_repository import TenderChunkRepository
from repositories.tender_file_repository import TenderFileRepository

router = APIRouter(prefix="/document", tags=["Summary"])

# Initialize dependencies
chunk_repo = TenderChunkRepository()
file_repo = TenderFileRepository()
embedding_service = EmbeddingService()
retrieval_service = RetrievalService(chunk_repo, embedding_service)
streaming_service = StreamingService(retrieval_service)


@router.post(
    "/{tender_file_id}/summarize",
    summary="Generate Document Summary (SSE Streaming)",
    description="Stream document summary generation in real-time"
)
async def summarize_document(
    tender_file_id: int = Path(..., description="Document ID", gt=0),
    request: SummaryRequest = None
):
    """
    Stream summary generation using Server-Sent Events (SSE).
    
    **Event Types:**
    - `status`: Progress updates
    - `token`: Individual response tokens (streaming summary text)
    - `complete`: Final complete summary
    - `error`: Error messages
    """
    # Check if document exists
    if not file_repo.exists(tender_file_id):
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Return SSE stream
    return StreamingResponse(
        streaming_service.stream_summary(
            tender_file_id=tender_file_id,
            explanation_level=request.explanation_level
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )