# routers/query_router.py
"""
Query Router with SSE Streaming Support
"""
from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import StreamingResponse
from dto.request_dto import QueryRequest
from dto.response_dto import QueryResponse
from services.streaming_service import StreamingService
from services.retrieval_service import RetrievalService
from services.embedding_service import EmbeddingService
from repositories.tender_chunk_repository import TenderChunkRepository
from repositories.tender_file_repository import TenderFileRepository

router = APIRouter(prefix="/document", tags=["Query"])

# Initialize dependencies
chunk_repo = TenderChunkRepository()
file_repo = TenderFileRepository()
embedding_service = EmbeddingService()
retrieval_service = RetrievalService(chunk_repo, embedding_service)
streaming_service = StreamingService(retrieval_service)


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
    
    **Event Types:**
    - `status`: Progress updates
    - `token`: Individual response tokens (streaming text)
    - `complete`: Final complete response with metadata
    - `error`: Error messages
    
    **Client Example (JavaScript):**
    ```javascript
    const eventSource = new EventSource('/document/1/query');
    
    eventSource.addEventListener('token', (e) => {
        console.log('Token:', e.data);
    });
    
    eventSource.addEventListener('complete', (e) => {
        const result = JSON.parse(e.data);
        console.log('Complete:', result);
        eventSource.close();
    });
    ```
    """
    # Check if document exists
    if not file_repo.exists(tender_file_id):
        raise HTTPException(status_code=404, detail="Document not found")
    
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


