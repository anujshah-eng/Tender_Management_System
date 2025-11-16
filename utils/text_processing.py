# utils/text_processing.py
"""
Text Processing Utilities
"""
import string
from typing import List

# Stopwords for BM25
STOPWORDS = {
    'that', 'this', 'with', 'from', 'have', 'will', 'your', 'their', 'which', 
    'were', 'been', 'there', 'would', 'about', 'should', 'could', 'these', 
    'those', 'shall', 'must', 'and', 'the', 'for', 'is', 'in', 'it', 'to', 
    'of', 'as', 'at', 'by', 'an', 'are', 'on', 'if', 'or', 'not', 'be', 'all'
}


def preprocess_text(text: str) -> List[str]:
    """
    Preprocess text for BM25: lowercase, remove punctuation, remove stopwords
    
    Args:
        text: Raw text string
        
    Returns:
        List of processed tokens
    """
    if not text:
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Tokenize and filter stopwords
    tokens = text.split()
    tokens = [token for token in tokens if token not in STOPWORDS and len(token) > 2]
    
    return tokens


def chunk_text(text: str, max_size: int, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        max_size: Maximum chunk size in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text or len(text) <= max_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for punct in ['. ', '! ', '? ', '\n\n']:
                last_break = text.rfind(punct, start, end)
                if last_break != -1:
                    end = last_break + 1
                    break
        
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return chunks

def truncate_for_embedding(text: str, max_chars: int) -> str:
    """
    Truncate text to maximum character limit for embedding generation
    
    Args:
        text: Text to truncate
        max_chars: Maximum number of characters allowed
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_chars:
        return text
    
    # Truncate at the limit
    truncated = text[:max_chars]
    
    # Try to break at last sentence boundary to avoid cutting mid-sentence
    for punct in ['. ', '! ', '? ', '\n\n']:
        last_break = truncated.rfind(punct)
        if last_break > max_chars * 0.8:  # Only use if we're not losing too much
            return truncated[:last_break + 1].strip()
    
    # If no good break point, just truncate
    return truncated.strip()