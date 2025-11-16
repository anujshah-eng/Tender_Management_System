#dto/request_dto/ingest_request.py
"""
Request DTOs for Document Ingestion
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime


class IngestRequest(BaseModel):
    """Request for ingesting a tender document"""
    file_url: HttpUrl = Field(..., description="URL of the PDF document to ingest")
    uploaded_by: str = Field(default="user", description="User who uploaded the document")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_url": "https://example.com/tender-document.pdf",
                "uploaded_by": "john_doe"
            }
        }