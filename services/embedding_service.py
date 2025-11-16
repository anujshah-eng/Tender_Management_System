"""
Embedding Service for generating embeddings with size limits
"""
import time
from typing import List, Dict
from collections import Counter
import google.generativeai as genai
from core.interfaces import IEmbeddingService
from config.model_config import model_config
from config.settings import settings
from core.exceptions import EmbeddingGenerationException
from utils.text_processing import truncate_for_embedding
import logging

logger = logging.getLogger(__name__)


class EmbeddingService(IEmbeddingService):
    """Service for generating dense and sparse embeddings"""
    
    def generate_dense_embedding(self, text: str, task_type: str) -> List[float]:
        """Generate dense embedding using Google's embedding model with size limits"""
        
        # Truncate text if too long
        original_length = len(text)
        text = truncate_for_embedding(text, settings.MAX_EMBEDDING_CHARS)
        
        if len(text) < original_length:
            logger.warning(f"Text truncated from {original_length} to {len(text)} chars for embedding")
        
        retries = 0
        while retries < settings.MAX_RETRIES:
            try:
                embedding = genai.embed_content(
                    model=model_config.get_embedding_model(),
                    content=text,
                    task_type=task_type
                )
                return embedding['embedding']
                
            except Exception as e:
                error_msg = str(e)
                
                # If payload too large, reduce text size more aggressively
                if "payload size exceeds" in error_msg.lower() or "too large" in error_msg.lower():
                    # Reduce by 50% and retry immediately
                    text = text[:len(text)//2]
                    logger.warning(f"Payload too large, reducing to {len(text)} chars")
                    if len(text) < 100:  # Minimum viable text
                        raise EmbeddingGenerationException("Text too short after reduction")
                    continue
                
                retries += 1
                if retries >= settings.MAX_RETRIES:
                    raise EmbeddingGenerationException(
                        f"Failed to generate embedding after {settings.MAX_RETRIES} retries: {e}"
                    )
                
                wait_time = 2 ** retries
                logger.warning(f"Embedding attempt {retries} failed, waiting {wait_time}s: {e}")
                time.sleep(wait_time)
        
        # Fallback zero vector
        logger.error("Returning zero vector as fallback")
        return [0.0] * 768
    
    def generate_sparse_embedding(self, tokens: List[str]) -> Dict[str, int]:
        """Generate sparse embedding (term frequency)"""
        return dict(Counter(tokens))
    
    def batch_generate_dense_embeddings(
        self, 
        texts: List[str], 
        task_type: str
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts with error handling"""
        embeddings = []
        failed_count = 0
        
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_dense_embedding(text, task_type)
                embeddings.append(embedding)
                
                # Add small delay to avoid rate limiting
                if i % 10 == 0 and i > 0:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Failed to generate embedding for chunk {i}: {e}")
                embeddings.append([0.0] * 768)  # Zero vector fallback
                failed_count += 1
        
        if failed_count > 0:
            logger.warning(f"Failed to generate {failed_count}/{len(texts)} embeddings")
        
        return embeddings
