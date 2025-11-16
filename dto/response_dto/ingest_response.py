"""
Response DTOs for Document Ingestion
"""
from pydantic import BaseModel, Field
from typing import Optional


class IngestStatus(BaseModel):
    """Real-time status updates during ingestion"""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Current status (processing/completed/failed)")
    message: str = Field(..., description="Human-readable status message")
    progress: Optional[float] = Field(None, ge=0.0, le=100.0, description="Progress percentage")
    current_step: Optional[str] = Field(None, description="Current processing step")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "status": "processing",
                "message": "Generating embeddings...",
                "progress": 45.5,
                "current_step": "embedding_generation"
            }
        }


class IngestResponse(BaseModel):
    """Response for document ingestion"""
    tender_file_id: Optional[int] = Field(None, description="Database ID of ingested tender file")
    status: str = Field(..., description="Processing status (success/failed/processing)")
    message: str = Field(..., description="Status message")
    progress: Optional[float] = Field(None, ge=0.0, le=100.0, description="Processing progress percentage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tender_file_id": 123,
                "status": "success",
                "message": "Document ingested successfully",
                "progress": 100.0
            }
        }


class DeleteResponse(BaseModel):
    """Response for tender deletion"""
    success: bool = Field(..., description="Whether deletion was successful")
    tender_file_id: int = Field(..., description="ID of deleted tender file")
    deleted_counts: dict = Field(..., description="Count of deleted records per table")
    message: str = Field(..., description="Deletion status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "tender_file_id": 123,
                "deleted_counts": {
                    "tender_chunks": 38,
                    "tender_files": 1,
                    "tender_projects": 1
                },
                "message": "Tender and all related data deleted successfully"
            }
        }