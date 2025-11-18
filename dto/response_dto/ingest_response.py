# dto/response_dto/ingest_response.py
"""
Response DTOs for Document Ingestion
"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class TenderDetails(BaseModel):
    """Extracted tender details from PDF"""
    tender_id: Optional[str] = Field(None, description="Unique tender identifier from document")
    project_title: Optional[str] = Field(None, description="Name of the project")
    issuing_authority: Optional[str] = Field(None, description="Organization issuing the tender")
    location: Optional[str] = Field(None, description="Project site location")
    project_value: Optional[str] = Field(None, description="Total estimated cost")
    emd_amount: Optional[str] = Field(None, description="Earnest Money Deposit amount")
    summary: Optional[str] = Field(None, description="Brief project summary (1-2 lines)")
    boq_document_link: Optional[str] = Field(None, description="Link to separate BOQ document if available")
    deadline: Optional[str] = Field(None, description="Project completion deadline/contract period")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tender_id": "TENDER-2024-001",
                "project_title": "Construction of Highway Bridge",
                "issuing_authority": "National Highways Authority",
                "location": "Mumbai, Maharashtra",
                "project_value": "₹50,00,00,000",
                "emd_amount": "₹50,00,000",
                "summary": "Construction and maintenance of 2km highway bridge with 4-lane capacity",
                "boq_document_link": "https://example.com/boq/tender-2024-001.pdf",
                "deadline": "12 months from date of award"
            }
        }


class IngestStatus(BaseModel):
    """Real-time status updates during ingestion"""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Current status (processing/completed/failed)")
    message: str = Field(..., description="Human-readable status message")
    current_step: Optional[str] = Field(None, description="Current processing step")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "status": "processing",
                "message": "Generating embeddings...",
                "current_step": "embedding_generation"
            }
        }


class IngestResponse(BaseModel):
    """Response for document ingestion"""
    # Core Response Fields
    tender_file_id: Optional[int] = Field(None, description="Database ID of ingested tender file")
    status: str = Field(..., description="Processing status (success/failed/processing)")
    message: str = Field(..., description="Status message")
    
    # Extracted Tender Details
    tender_details: Optional[TenderDetails] = Field(None, description="Extracted tender information from PDF")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tender_file_id": 123,
                "status": "success",
                "message": "Document ingested successfully",
                "tender_details": {
                    "tender_id": "TENDER-2024-001",
                    "project_title": "Construction of Highway Bridge",
                    "issuing_authority": "National Highways Authority",
                    "location": "Mumbai, Maharashtra",
                    "project_value": "₹50,00,00,000",
                    "emd_amount": "₹50,00,000",
                    "summary": "Construction and maintenance of 2km highway bridge",
                    "boq_document_link": "https://example.com/boq/tender-2024-001.pdf",
                    "deadline": "12 months from date of award"
                }
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