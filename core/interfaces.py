#core/interfaces.py
"""
Core Interfaces (Dependency Inversion)
Define contracts that outer layers must implement
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator 
from .domain_models import TenderProject, TenderFile, TenderChunk, ChunkSearchResult

class ITenderProjectRepository(ABC):
    """Interface for TenderProject repository"""
    
    @abstractmethod
    def create(self, project: TenderProject) -> int:
        """Create a new tender project"""
        pass
    
    @abstractmethod
    def get_by_id(self, tender_id: int) -> Optional[TenderProject]:
        """Get project by ID"""
        pass
    
    @abstractmethod
    def update(self, project: TenderProject) -> bool:
        """Update existing project"""
        pass


class ITenderFileRepository(ABC):
    """Interface for TenderFile repository"""
    
    @abstractmethod
    def create(self, file: TenderFile) -> int:
        """Create a new tender file"""
        pass
    
    @abstractmethod
    def get_by_id(self, tender_file_id: int) -> Optional[TenderFile]:
        """Get file by ID"""
        pass
    
    @abstractmethod
    def update_summary(self, tender_file_id: int, summary: str, simple_summary: str) -> bool:
        """Update summaries"""
        pass
    
    @abstractmethod
    def exists(self, tender_file_id: int) -> bool:
        """Check if file exists"""
        pass


class ITenderChunkRepository(ABC):
    """Interface for TenderChunk repository"""
    
    @abstractmethod
    def bulk_create(self, chunks: List[TenderChunk]) -> bool:
        """Create multiple chunks"""
        pass
    
    @abstractmethod
    def get_all_by_file_id(self, tender_file_id: int) -> List[TenderChunk]:
        """Get all chunks for a file"""
        pass
    
    @abstractmethod
    def hybrid_search(
        self, 
        tender_file_id: int,
        query_embedding: List[float],
        query_tokens: List[str],
        top_k: int,
        alpha: float
    ) -> List[ChunkSearchResult]:
        """Perform hybrid search"""
        pass


class IEmbeddingService(ABC):
    """Interface for embedding generation"""
    
    @abstractmethod
    def generate_dense_embedding(self, text: str, task_type: str) -> List[float]:
        """Generate dense embedding"""
        pass
    
    @abstractmethod
    def generate_sparse_embedding(self, tokens: List[str]) -> Dict[str, int]:
        """Generate sparse embedding"""
        pass


class IStreamingService(ABC):
    """Interface for SSE streaming"""
    
    @abstractmethod
    async def stream_summary(
        self, 
        tender_file_id: int, 
        explanation_level: str
    ) -> AsyncGenerator[str, None]:
        """Stream summary generation"""
        pass
    
    @abstractmethod
    async def stream_qa_response(
        self, 
        tender_file_id: int,
        question: str,
        explanation_level: str
    ) -> AsyncGenerator[str, None]:
        """Stream Q&A response"""
        pass