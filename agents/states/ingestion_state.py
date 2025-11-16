#Agents/states/ingestion_state.py
"""
State Definitions for Ingestion Workflow
"""
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class TenderIngestionState(TypedDict):
    """State for document ingestion workflow"""
    # Input
    project_id: int
    tender_number: str
    file_url: str
    uploaded_by: str
    tender_date: Optional[datetime]
    submission_deadline: Optional[datetime]
    generate_summary: bool
    
    # Processing
    tender_id: int
    tender_file_id: int
    raw_text: str
    structured_data: Dict[str, Any]
    chunks: List[Dict[str, Any]]
    
    # Embeddings
    dense_embeddings: List[List[float]]
    sparse_embeddings: List[Dict[str, int]]
    hybrid_embeddings: List[Dict[str, Any]]
    
    # Status
    db_status: str
    error: str
