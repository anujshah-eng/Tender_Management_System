# services/retrieval_service.py
"""
Retrieval Service for searching and fetching chunks
"""
import logging
from typing import List
from core.domain_models import TenderChunk, ChunkSearchResult
from repositories.tender_chunk_repository import TenderChunkRepository
from services.embedding_service import EmbeddingService
from config.settings import settings
from utils.text_processing import preprocess_text

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for retrieving relevant document chunks"""
    
    def __init__(
        self,
        chunk_repository: TenderChunkRepository,
        embedding_service: EmbeddingService
    ):
        self.chunk_repository = chunk_repository
        self.embedding_service = embedding_service
        logger.info("RetrievalService initialized")
    
    def get_all_chunks(self, tender_file_id: int) -> List[TenderChunk]:
        """Get all chunks for a document"""
        logger.debug(f"Retrieving all chunks for tender_file_id={tender_file_id}")
        chunks = self.chunk_repository.get_all_by_file_id(tender_file_id)
        logger.info(f"Retrieved {len(chunks)} chunks for tender_file_id={tender_file_id}")
        return chunks
    
    def retrieve_relevant_chunks(
        self,
        tender_file_id: int,
        query: str,
        top_k: int = None
    ) -> List[ChunkSearchResult]:
        """Retrieve most relevant chunks using hybrid search"""
        
        if top_k is None:
            top_k = settings.TOP_K_CHUNKS
        
        logger.info("="*70)
        logger.info("RETRIEVING RELEVANT CHUNKS")
        logger.info("="*70)
        logger.info(f"Tender File ID: {tender_file_id}")
        logger.info(f"Query: {query}")
        logger.info(f"Top K: {top_k}")
        logger.info(f"Hybrid Alpha: {settings.HYBRID_SEARCH_ALPHA}")
        
        # Generate query embeddings
        logger.debug("Generating query embeddings...")
        query_embedding = self.embedding_service.generate_dense_embedding(
            text=query,
            task_type="retrieval_query"
        )
        logger.debug(f"Generated dense embedding with {len(query_embedding)} dimensions")
        
        query_tokens = preprocess_text(query)
        logger.debug(f"Tokenized query into {len(query_tokens)} tokens: {query_tokens[:10]}...")
        
        # Perform hybrid search
        logger.info("Performing hybrid search...")
        results = self.chunk_repository.hybrid_search(
            tender_file_id=tender_file_id,
            query_embedding=query_embedding,
            query_tokens=query_tokens,
            top_k=top_k,
            alpha=settings.HYBRID_SEARCH_ALPHA
        )
        
        logger.info(f"Found {len(results)} relevant chunks")
        
        if results:
            logger.info("Top 3 results:")
            for i, result in enumerate(results[:3], 1):
                logger.info(f"  {i}. Score: {result.relevance_score:.4f}, Chunk: {result.chunk.chunk_index}")
                logger.debug(f"     Preview: {result.chunk.chunk_text[:100]}...")
        
        logger.info("="*70)
        
        return results