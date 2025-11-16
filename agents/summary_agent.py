#Agent/summary_agent.py
"""
Summary Agent - Handles document summarization
"""
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from services.retrieval_service import RetrievalService
from config.model_config import model_config
from core.domain_models import TenderChunk


class SummaryAgent(BaseAgent):
    """Agent for generating document summaries"""
    
    def __init__(self, retrieval_service: RetrievalService):
        super().__init__("SummaryAgent")
        self.retrieval_service = retrieval_service
    
    def validate_input(self, **kwargs) -> bool:
        """Validate summary input"""
        return 'tender_file_id' in kwargs
    
    def process(self, **kwargs) -> Dict[str, Any]:
        """Process summary generation"""
        tender_file_id = kwargs.get('tender_file_id')
        explanation_level = kwargs.get('explanation_level', 'professional')
        
        self.logger.info(f"Generating summary for document {tender_file_id}")
        
        # Get all chunks
        chunks = self.retrieval_service.get_all_chunks(tender_file_id)
        
        if not chunks:
            return {
                "success": False,
                "error": "No document content found"
            }
        
        # Prepare context
        context = self._prepare_summary_context(chunks, explanation_level)
        
        # Generate summary
        model = model_config.get_summary_model()
        response = model.generate_content(context)
        
        # Extract key points
        key_points = self._extract_key_points(response.text)
        
        return {
            "success": True,
            "summary": response.text,
            "key_points": key_points,
            "total_chunks": len(chunks),
            "chunks_processed": len(chunks)
        }
    
    def _prepare_summary_context(
        self, 
        chunks: List[TenderChunk],
        explanation_level: str
    ) -> str:
        """Prepare context for summary generation"""
        combined_text = "\n\n".join([chunk.chunk_text for chunk in chunks])
        
        if explanation_level == "simple":
            prompt = f"""
You are summarizing a tender document for someone new to tenders.
Use simple language, short sentences, and explain technical terms.

Document content:
{combined_text}

Provide a clear, simple summary that covers:
1. What the tender is about
2. Who can apply
3. Important deadlines
4. Key requirements

Keep it friendly and easy to understand.
"""
        else:
            prompt = f"""
You are a professional tender analyst. Provide a comprehensive summary.

Document content:
{combined_text}

Provide a structured summary covering:
1. Tender Overview
2. Scope of Work
3. Eligibility Criteria
4. Submission Requirements
5. Timeline and Deadlines
6. Evaluation Criteria

Use professional terminology and be precise.
"""
        return prompt
    
    def _extract_key_points(self, summary_text: str) -> List[str]:
        """Extract key points from summary"""
        # Simple extraction logic - can be enhanced
        lines = summary_text.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
                # Remove numbering/bullets
                point = line.lstrip('0123456789.•- ')
                if point:
                    key_points.append(point)
        
        return key_points[:10]  # Return top 10 key points

