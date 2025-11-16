#Agent/qyery_agent.py
"""
Query Agent - Handles Q&A operations
"""
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from services.retrieval_service import RetrievalService
from config.model_config import model_config
from core.domain_models import ChunkSearchResult


class QueryAgent(BaseAgent):
    """Agent for answering questions about documents"""
    
    def __init__(self, retrieval_service: RetrievalService):
        super().__init__("QueryAgent")
        self.retrieval_service = retrieval_service
    
    def validate_input(self, **kwargs) -> bool:
        """Validate query input"""
        return 'tender_file_id' in kwargs and 'question' in kwargs
    
    def process(self, **kwargs) -> Dict[str, Any]:
        """Process query and generate answer"""
        tender_file_id = kwargs.get('tender_file_id')
        question = kwargs.get('question')
        explanation_level = kwargs.get('explanation_level', 'professional')
        top_k = kwargs.get('top_k', 5)
        
        self.logger.info(f"Processing query for document {tender_file_id}")
        
        # Retrieve relevant chunks
        search_results = self.retrieval_service.retrieve_relevant_chunks(
            tender_file_id=tender_file_id,
            query=question,
            top_k=top_k
        )
        
        if not search_results:
            return {
                "success": False,
                "error": "No relevant information found"
            }
        
        # Prepare context
        context = self._prepare_context(question, search_results, explanation_level)
        
        # Generate answer
        model = model_config.get_qa_model()
        response = model.generate_content(context)
        
        return {
            "success": True,
            "answer": response.text,
            "chunks_used": len(search_results),
            "top_relevance": search_results[0].relevance_score if search_results else 0,
            "source_chunks": [
                {
                    "chunk_id": result.chunk.id,
                    "chunk_index": result.chunk.chunk_index,
                    "relevance_score": result.relevance_score,
                    "preview": result.chunk.chunk_text[:200]
                }
                for result in search_results
            ]
        }
    
    def _prepare_context(
        self, 
        question: str, 
        search_results: List[ChunkSearchResult],
        explanation_level: str
    ) -> str:
        """Prepare context for answer generation"""
        context_chunks = "\n\n".join([
            f"[Section {i+1}]\n{result.chunk.chunk_text}"
            for i, result in enumerate(search_results)
        ])
        
        if explanation_level == "simple":
            prompt = f"""
You are helping someone understand a tender document.
Use simple words and short sentences.

Relevant sections from the document:
{context_chunks}

Question: {question}

Provide a clear, simple answer. Explain any technical terms.
"""
        else:
            prompt = f"""
You are a professional tender consultant.

Relevant sections from the document:
{context_chunks}

Question: {question}

Provide a precise, professional answer based on the document sections.
"""
        return prompt