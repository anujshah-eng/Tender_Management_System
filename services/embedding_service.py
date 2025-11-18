# services/embedding_service.py
"""
Embedding Service for generating embeddings with size limits
"""
import time
import logging
from typing import List, Dict
from collections import Counter
import google.generativeai as genai
from core.interfaces import IEmbeddingService
from config.model_config import model_config
from config.settings import settings
from core.exceptions import EmbeddingGenerationException
from utils.text_processing import truncate_for_embedding

logger = logging.getLogger(__name__)


class EmbeddingService(IEmbeddingService):
    """Service for generating dense and sparse embeddings"""
    
    def __init__(self):
        logger.info("Initializing EmbeddingService")
        logger.debug(f"Embedding model: {settings.EMBEDDING_MODEL}")
        logger.debug(f"Max embedding chars: {settings.MAX_EMBEDDING_CHARS}")
    
    def generate_dense_embedding(self, text: str, task_type: str) -> List[float]:
        """Generate dense embedding using Google's embedding model with size limits"""
        
        # Truncate text if too long
        original_length = len(text)
        text = truncate_for_embedding(text, settings.MAX_EMBEDDING_CHARS)
        
        if len(text) < original_length:
            logger.warning(f"Text truncated from {original_length} to {len(text)} chars for embedding")
        
        logger.debug(f"Generating dense embedding for {len(text)} chars, task_type={task_type}")
        
        retries = 0
        while retries < settings.MAX_RETRIES:
            try:
                embedding = genai.embed_content(
                    model=model_config.get_embedding_model(),
                    content=text,
                    task_type=task_type
                )
                logger.debug(f"Successfully generated embedding with {len(embedding['embedding'])} dimensions")
                return embedding['embedding']
                
            except Exception as e:
                error_msg = str(e)
                
                # If payload too large, reduce text size more aggressively
                if "payload size exceeds" in error_msg.lower() or "too large" in error_msg.lower():
                    text = text[:len(text)//2]
                    logger.warning(f"Payload too large, reducing to {len(text)} chars")
                    if len(text) < 100:
                        raise EmbeddingGenerationException("Text too short after reduction")
                    continue
                
                retries += 1
                if retries >= settings.MAX_RETRIES:
                    logger.error(f"Failed to generate embedding after {settings.MAX_RETRIES} retries: {e}")
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
        logger.debug(f"Generating sparse embedding for {len(tokens)} tokens")
        sparse = dict(Counter(tokens))
        logger.debug(f"Generated sparse embedding with {len(sparse)} unique terms")
        return sparse
    
    def batch_generate_dense_embeddings(
        self, 
        texts: List[str], 
        task_type: str
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts with error handling"""
        logger.info(f"Batch generating embeddings for {len(texts)} texts")
        embeddings = []
        failed_count = 0
        
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_dense_embedding(text, task_type)
                embeddings.append(embedding)
                
                if i % 10 == 0 and i > 0:
                    logger.debug(f"Progress: {i}/{len(texts)} embeddings generated")
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Failed to generate embedding for chunk {i}: {e}")
                embeddings.append([0.0] * 768)
                failed_count += 1
        
        if failed_count > 0:
            logger.warning(f"Failed to generate {failed_count}/{len(texts)} embeddings")
        
        logger.info(f"Batch embedding complete: {len(texts) - failed_count}/{len(texts)} successful")
        return embeddings