# routers/query_router.py
"""
Query Router with SSE Streaming Support
"""
import logging
from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import StreamingResponse
from dto.request_dto import QueryRequest
from dto.response_dto import QueryResponse
from services.streaming_service import StreamingService
from services.retrieval_service import RetrievalService
from services.embedding_service import EmbeddingService
from repositories.tender_chunk_repository import TenderChunkRepository
from repositories.tender_file_repository import TenderFileRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/document", tags=["Query"])

# Initialize dependencies
chunk_repo = TenderChunkRepository()
file_repo = TenderFileRepository()
embedding_service = EmbeddingService()
retrieval_service = RetrievalService(chunk_repo, embedding_service)
streaming_service = StreamingService(retrieval_service)

logger.info("Query router initialized")


@router.post(
    "/{tender_file_id}/query",
    summary="Ask a Question (SSE Streaming)",
    description="Stream answers to questions about a tender document in real-time"
)
async def query_document(
    tender_file_id: int = Path(..., description="Document ID", gt=0),
    request: QueryRequest = None
):
    """
    Stream Q&A response using Server-Sent Events (SSE).
    """
    logger.info("="*70)
    logger.info("QUERY REQUEST RECEIVED")
    logger.info("="*70)
    logger.info(f"Tender File ID: {tender_file_id}")
    logger.info(f"Question: {request.question}")
    logger.info(f"Explanation Level: {request.explanation_level}")
    logger.info(f"Top K: {request.top_k_chunks}")
    
    # Check if document exists
    if not file_repo.exists(tender_file_id):
        logger.error(f"Document not found: tender_file_id={tender_file_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    logger.info("Document found, starting streaming response")
    
    # Return SSE stream
    return StreamingResponse(
        streaming_service.stream_qa_response(
            tender_file_id=tender_file_id,
            question=request.question,
            explanation_level=request.explanation_level
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
