#dto/response_dto/query_response.py
"""
Response DTOs for Query Operations
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChunkReference(BaseModel):
    """Reference to a document chunk used in response"""
    chunk_id: int = Field(..., description="Database ID of chunk")
    chunk_index: int = Field(..., description="Index of chunk in document")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    preview: str = Field(..., max_length=200, description="Short preview of chunk content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": 501,
                "chunk_index": 3,
                "relevance_score": 0.89,
                "preview": "Eligibility criteria: Applicants must be registered contractors with at least 5 years..."
            }
        }


class QueryResponse(BaseModel):
    """Response for Q&A query"""
    success: bool = Field(..., description="Whether query was successful")
    answer: str = Field(..., description="Generated answer to the question")
    
    # Source Information
    chunks_used: int = Field(..., description="Number of chunks used to generate answer")
    source_chunks: List[ChunkReference] = Field(
        default_factory=list,
        description="References to source chunks"
    )
    
    # Confidence Metrics
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the answer"
    )
    top_relevance: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Relevance score of most relevant chunk"
    )
    
    # Metadata
    question: str = Field(..., description="Original question asked")
    explanation_level: str = Field(..., description="Explanation level used")
    response_time: Optional[float] = Field(None, description="Time taken to generate response (seconds)")
    generated_at: Optional[datetime] = Field(None, description="When response was generated")
    
    # Additional Information
    related_sections: List[str] = Field(
        default_factory=list,
        description="Suggested related sections to explore"
    )
    
    # Error Handling
    error: Optional[str] = Field(None, description="Error message if query failed")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "answer": "The eligibility criteria require contractors to be registered with...",
                "chunks_used": 3,
                "source_chunks": [],
                "confidence_score": 0.87,
                "top_relevance": 0.92,
                "question": "What are the eligibility criteria?",
                "explanation_level": "professional",
                "response_time": 2.3,
                "generated_at": "2024-01-15T14:35:00Z",
                "related_sections": ["submission requirements", "document checklist"]
            }
        }


class BatchQueryResponse(BaseModel):
    """Response for batch queries"""
    success: bool = Field(..., description="Whether batch processing was successful")
    total_questions: int = Field(..., description="Total questions processed")
    successful_answers: int = Field(..., description="Number of successful answers")
    
    # Results
    results: List[QueryResponse] = Field(
        default_factory=list,
        description="Individual query responses"
    )
    
    # Performance
    total_processing_time: Optional[float] = Field(
        None,
        description="Total time for all queries (seconds)"
    )
    average_response_time: Optional[float] = Field(
        None,
        description="Average time per query (seconds)"
    )
    
    # Error Summary
    errors: List[str] = Field(
        default_factory=list,
        description="Errors encountered during processing"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_questions": 3,
                "successful_answers": 3,
                "results": [],
                "total_processing_time": 8.5,
                "average_response_time": 2.83,
                "errors": []
            }
        }
