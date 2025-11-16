# services/retrieval_service.py
"""
Retrieval Service for searching and fetching chunks
"""
from typing import List
from core.domain_models import TenderChunk, ChunkSearchResult
from repositories.tender_chunk_repository import TenderChunkRepository
from services.embedding_service import EmbeddingService
from config.settings import settings
from utils.text_processing import preprocess_text


class RetrievalService:
    """Service for retrieving relevant document chunks"""
    
    def __init__(
        self,
        chunk_repository: TenderChunkRepository,
        embedding_service: EmbeddingService
    ):
        self.chunk_repository = chunk_repository
        self.embedding_service = embedding_service
    
    def get_all_chunks(self, tender_file_id: int) -> List[TenderChunk]:
        """Get all chunks for a document"""
        return self.chunk_repository.get_all_by_file_id(tender_file_id)
    
    def retrieve_relevant_chunks(
        self,
        tender_file_id: int,
        query: str,
        top_k: int = None
    ) -> List[ChunkSearchResult]:
        """Retrieve most relevant chunks using hybrid search"""
        
        if top_k is None:
            top_k = settings.TOP_K_CHUNKS
        
        # Generate query embeddings
        query_embedding = self.embedding_service.generate_dense_embedding(
            text=query,
            task_type="retrieval_query"
        )
        
        query_tokens = preprocess_text(query)
        
        # Perform hybrid search
        results = self.chunk_repository.hybrid_search(
            tender_file_id=tender_file_id,
            query_embedding=query_embedding,
            query_tokens=query_tokens,
            top_k=top_k,
            alpha=settings.HYBRID_SEARCH_ALPHA
        )
        
        return results