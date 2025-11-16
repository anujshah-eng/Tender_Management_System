#dto/request_dto/query_request.py
"""
Request DTOs for Querying Documents
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class QueryRequest(BaseModel):
    """Request for Q&A on tender documents"""
    question: str = Field(
        ..., 
        min_length=3,
        max_length=500,
        description="Question to ask about the tender document"
    )
    explanation_level: Literal["simple", "professional"] = Field(
        default="professional",
        description="Response complexity level (simple for non-experts, professional for detailed)"
    )
    top_k_chunks: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of relevant chunks to retrieve"
    )
    include_sources: bool = Field(
        default=True,
        description="Whether to include source chunk references"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the eligibility criteria for this tender?",
                "explanation_level": "professional",
                "top_k_chunks": 5,
                "include_sources": True
            }
        }


