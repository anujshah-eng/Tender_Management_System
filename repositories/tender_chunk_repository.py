# repositories/tender_chunk_repository.py
"""
TenderChunk Repository with SQLAlchemy
"""
import logging
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from repositories.base_repository import BaseRepository
from database.models import TenderChunk
from core.interfaces import ITenderChunkRepository
from core.domain_models import TenderChunk as DomainTenderChunk, ChunkSearchResult
from database.connection import get_db_session

logger = logging.getLogger(__name__)


class TenderChunkRepository(BaseRepository[TenderChunk], ITenderChunkRepository):
    """Repository for TenderChunk operations"""
    
    def __init__(self):
        super().__init__(TenderChunk)
        logger.debug("TenderChunkRepository initialized")
    
    def bulk_create(self, chunks: List[DomainTenderChunk]) -> bool:
        """Create multiple chunks efficiently"""
        if not chunks:
            logger.warning("No chunks to create")
            return True
        
        logger.info(f"Bulk creating {len(chunks)} chunks")
        
        with get_db_session() as db:
            db_chunks = []
            for chunk in chunks:
                db_chunk = TenderChunk(
                    tender_file_id=chunk.tender_file_id,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    chunk_metadata=chunk.chunk_metadata,
                    dense_embedding=chunk.dense_embedding,
                    sparse_embedding=chunk.sparse_embedding,
                    bm25_tokens=chunk.bm25_tokens
                )
                db_chunks.append(db_chunk)
            
            db.bulk_save_objects(db_chunks)
            db.flush()
            logger.info(f"Successfully created {len(db_chunks)} chunks")
            return True
    
    def get_all_by_file_id(self, tender_file_id: int) -> List[DomainTenderChunk]:
        """Get all chunks for a file"""
        logger.debug(f"Fetching all chunks for tender_file_id={tender_file_id}")
        
        with get_db_session() as db:
            chunks = db.query(TenderChunk).filter(
                TenderChunk.tender_file_id == tender_file_id
            ).order_by(TenderChunk.chunk_index).all()
            
            logger.debug(f"Found {len(chunks)} chunks")
            
            return [
                DomainTenderChunk(
                    id=chunk.id,
                    tender_file_id=chunk.tender_file_id,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    chunk_metadata=chunk.chunk_metadata,
                    bm25_tokens=chunk.bm25_tokens,
                    created_at=chunk.created_at
                )
                for chunk in chunks
            ]
    
    def hybrid_search(
        self, 
        tender_file_id: int,
        query_embedding: List[float],
        query_tokens: List[str],
        top_k: int,
        alpha: float
    ) -> List[ChunkSearchResult]:
        """Perform hybrid search (dense + BM25)"""
        logger.info(f"Performing hybrid search: tender_file_id={tender_file_id}, top_k={top_k}, alpha={alpha}")
        logger.debug(f"Query embedding dimensions: {len(query_embedding)}")
        logger.debug(f"Query tokens: {len(query_tokens)} tokens")
        
        with get_db_session() as db:
            query_text = ' '.join(query_tokens)
            beta = 1 - alpha
            
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            logger.debug("Executing hybrid search SQL query...")
            
            # Hybrid search query
            sql = text("""
                WITH dense_scores AS (
                    SELECT 
                        id,
                        1 - (dense_embedding <=> CAST(:embedding AS vector)) AS dense_score
                    FROM tender_chunks
                    WHERE tender_file_id = :file_id
                ),
                bm25_scores AS (
                    SELECT 
                        id,
                        ts_rank(to_tsvector('english', chunk_text), 
                               plainto_tsquery('english', :query_text)) AS bm25_score
                    FROM tender_chunks
                    WHERE tender_file_id = :file_id
                )
                SELECT 
                    tc.id,
                    tc.chunk_text,
                    tc.chunk_metadata,
                    tc.chunk_index,
                    (COALESCE(ds.dense_score, 0) * :alpha + 
                     COALESCE(bs.bm25_score, 0) * :beta) AS combined_score
                FROM tender_chunks tc
                LEFT JOIN dense_scores ds ON tc.id = ds.id
                LEFT JOIN bm25_scores bs ON tc.id = bs.id
                WHERE tc.tender_file_id = :file_id
                ORDER BY combined_score DESC
                LIMIT :top_k;
            """)
            
            results = db.execute(sql, {
                'embedding': embedding_str,
                'file_id': tender_file_id,
                'query_text': query_text,
                'alpha': alpha,
                'beta': beta,
                'top_k': top_k
            }).fetchall()
            
            logger.info(f"Hybrid search returned {len(results)} results")
            
            search_results = []
            for rank, row in enumerate(results, 1):
                chunk = DomainTenderChunk(
                    id=row[0],
                    chunk_text=row[1],
                    chunk_metadata=row[2],
                    chunk_index=row[3],
                    tender_file_id=tender_file_id
                )
                result = ChunkSearchResult(
                    chunk=chunk,
                    relevance_score=float(row[4]),
                    rank=rank
                )
                search_results.append(result)
                logger.debug(f"  Rank {rank}: Score={result.relevance_score:.4f}, Chunk={chunk.chunk_index}")
            
            return search_results