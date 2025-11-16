#dto/response_dto/summary_response.py
"""
Response DTOs for Summary Operations
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SummaryResponse(BaseModel):
    """Response for document summary"""
    success: bool = Field(..., description="Whether summary generation was successful")
    summary: str = Field(..., description="Generated document summary")
    
    # Summary Structure
    key_points: List[str] = Field(
        default_factory=list,
        description="Key points extracted from document"
    )
    sections_covered: List[str] = Field(
        default_factory=list,
        description="Document sections included in summary"
    )
    
    # Processing Information
    total_chunks: int = Field(..., description="Total chunks in document")
    chunks_processed: int = Field(..., description="Chunks processed for summary")
    
    # Metadata
    explanation_level: str = Field(..., description="Summary complexity level")
    word_count: Optional[int] = Field(None, description="Word count of summary")
    processing_time: Optional[float] = Field(None, description="Time taken to generate summary (seconds)")
    generated_at: Optional[datetime] = Field(None, description="When summary was generated")
    
    # Document Information
    tender_file_id: int = Field(..., description="ID of summarized document")
    document_title: Optional[str] = Field(None, description="Title of the document")
    
    # Error Handling
    error: Optional[str] = Field(None, description="Error message if summary failed")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "summary": "This tender is for construction services requiring...",
                "key_points": [
                    "Total estimated value: $500,000",
                    "Submission deadline: February 15, 2024",
                    "Minimum experience: 5 years"
                ],
                "sections_covered": [
                    "Project Overview",
                    "Eligibility",
                    "Timeline",
                    "Requirements"
                ],
                "total_chunks": 38,
                "chunks_processed": 38,
                "explanation_level": "professional",
                "word_count": 450,
                "processing_time": 5.7,
                "generated_at": "2024-01-15T14:40:00Z",
                "tender_file_id": 123,
                "document_title": "Construction Tender 2024"
            }
        }