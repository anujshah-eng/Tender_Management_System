#dto/request_dto/summary_request.py
"""
Request DTOs for Document Summarization
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class SummaryRequest(BaseModel):
    """Request for document summary generation"""
    explanation_level: Literal["simple", "professional"] = Field(
        default="professional",
        description="Summary complexity level"
    )
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific areas to focus on (e.g., ['eligibility', 'timeline', 'requirements'])"
    )
    max_length: Optional[Literal["brief", "detailed", "comprehensive"]] = Field(
        default="detailed",
        description="Desired summary length"
    )
    include_key_points: bool = Field(
        default=True,
        description="Whether to extract key points separately"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "explanation_level": "simple",
                "focus_areas": ["eligibility", "deadlines", "requirements"],
                "max_length": "detailed",
                "include_key_points": True
            }
        }
