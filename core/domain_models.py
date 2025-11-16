#core/domain_models.py
"""
Core Domain Models
These represent the business entities
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal


@dataclass
class TenderProject:
    """Domain model for Tender Project"""
    tender_id: Optional[int] = None
    project_id: int = None
    tender_number: str = None
    tender_date: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    tender_status: str = "Open"
    tender_value: Decimal = Decimal("0.00")
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass
class TenderFile:
    """Domain model for Tender File"""
    tender_file_id: Optional[int] = None
    tender_id: int = None
    file_name: str = None
    file_path: str = None
    file_type: str = "pdf"
    version: int = 1
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    summary: Optional[str] = None
    simple_summary: Optional[str] = None
    bm25_corpus: Optional[Dict[str, Any]] = None


@dataclass
class TenderChunk:
    """Domain model for Tender Chunk"""
    id: Optional[int] = None
    tender_file_id: int = None
    chunk_index: int = None
    chunk_text: str = None
    chunk_metadata: Optional[Dict[str, Any]] = None
    dense_embedding: Optional[List[float]] = None
    sparse_embedding: Optional[Dict[str, int]] = None
    bm25_tokens: Optional[List[str]] = None
    created_at: Optional[datetime] = None


@dataclass
class ChunkSearchResult:
    """Result from chunk retrieval"""
    chunk: TenderChunk
    relevance_score: float
    rank: int