# workflows/workflow_states.py
"""
Workflow State Definitions for LangGraph
"""
from typing import TypedDict, List, Dict, Any, Literal, Optional


class TenderIngestionState(TypedDict):
    """State for document ingestion workflow"""
    project_id: int
    tender_number: str
    file_url: str
    tender_id: int
    tender_file_id: int
    raw_text: str
    structured_data: Dict[str, Any]
    
    # Enhanced Tender Details
    extracted_tender_details: Dict[str, Any]
    
    chunks: List[Dict[str, Any]]
    dense_embeddings: List[List[float]]
    sparse_embeddings: List[Dict[str, int]]
    hybrid_embeddings: List[Dict[str, Any]]
    db_status: str
    error: str


class AgentQueryState(TypedDict):
    """State for agent query workflow"""
    tender_file_id: int
    user_query: str
    agent_type: Literal["summary", "qa"]
    explanation_level: Literal["simple", "professional"]
    retrieved_chunks: List[Dict[str, Any]]
    response: str
    error: str