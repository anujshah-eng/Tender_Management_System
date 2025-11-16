# services/streaming_service.py
"""
SSE Streaming Service for Real-time Responses
"""
import json
import asyncio
from typing import AsyncGenerator
from core.interfaces import IStreamingService
from services.retrieval_service import RetrievalService
from config.model_config import model_config
from config.settings import settings
from core.exceptions import DocumentNotFoundException


class StreamingService(IStreamingService):
    """Handles SSE streaming for Q&A and Summary generation"""
    
    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval_service = retrieval_service
    
    async def stream_summary(
        self, 
        tender_file_id: int, 
        explanation_level: str
    ) -> AsyncGenerator[str, None]:
        """Stream summary generation with SSE"""
        try:
            # Yield initial status
            yield self._create_sse_event("status", "Retrieving document chunks...")
            await asyncio.sleep(0.1)
            
            # Get all chunks
            chunks = self.retrieval_service.get_all_chunks(tender_file_id)
            
            if not chunks:
                raise DocumentNotFoundException(f"No chunks found for file {tender_file_id}")
            
            yield self._create_sse_event("status", f"Processing {len(chunks)} chunks...")
            await asyncio.sleep(0.1)
            
            # Prepare context
            context = self._prepare_summary_context(chunks, explanation_level)
            
            yield self._create_sse_event("status", "Generating summary...")
            await asyncio.sleep(0.1)
            
            # Get streaming model
            model = model_config.get_streaming_model(
                temperature=settings.SUMMARY_TEMPERATURE
            )
            
            # Stream the response
            full_response = ""
            response = model.generate_content(context, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    yield self._create_sse_event("token", chunk.text)
                    await asyncio.sleep(0.01)  # Small delay for smooth streaming
            
            # Send completion
            yield self._create_sse_event("complete", full_response)
            
        except Exception as e:
            yield self._create_sse_event("error", str(e))
    
    async def stream_qa_response(
        self, 
        tender_file_id: int,
        question: str,
        explanation_level: str
    ) -> AsyncGenerator[str, None]:
        """Stream Q&A response with SSE"""
        try:
            # Yield initial status
            yield self._create_sse_event("status", "Searching relevant sections...")
            await asyncio.sleep(0.1)
            
            # Retrieve relevant chunks
            search_results = self.retrieval_service.retrieve_relevant_chunks(
                tender_file_id=tender_file_id,
                query=question,
                top_k=settings.TOP_K_CHUNKS
            )
            
            if not search_results:
                yield self._create_sse_event("error", "No relevant information found")
                return
            
            yield self._create_sse_event("status", f"Found {len(search_results)} relevant sections...")
            await asyncio.sleep(0.1)
            
            # Prepare context
            context = self._prepare_qa_context(question, search_results, explanation_level)
            
            yield self._create_sse_event("status", "Generating answer...")
            await asyncio.sleep(0.1)
            
            # Get streaming model
            model = model_config.get_streaming_model(
                temperature=settings.QA_TEMPERATURE
            )
            
            # Stream the response
            full_response = ""
            response = model.generate_content(context, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    yield self._create_sse_event("token", chunk.text)
                    await asyncio.sleep(0.01)
            
            # Send completion with metadata
            completion_data = {
                "answer": full_response,
                "chunks_used": len(search_results),
                "top_relevance": search_results[0].relevance_score if search_results else 0
            }
            yield self._create_sse_event("complete", json.dumps(completion_data))
            
        except Exception as e:
            yield self._create_sse_event("error", str(e))
    
    def _create_sse_event(self, event_type: str, data: str) -> str:
        """Create SSE formatted event"""
        return f"event: {event_type}\ndata: {data}\n\n"
    
    def _prepare_summary_context(self, chunks, explanation_level: str) -> str:
        """Prepare context for summary generation"""
        combined_text = "\n\n".join([chunk.chunk_text for chunk in chunks])
        
        if explanation_level == "simple":
            prompt = f"""
You are summarizing a tender document for a 14-year-old student.
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
    
    def _prepare_qa_context(self, question: str, search_results, explanation_level: str) -> str:
        """Prepare context for Q&A"""
        context_chunks = "\n\n".join([
            f"[Section {i+1}]\n{result.chunk.chunk_text}"
            for i, result in enumerate(search_results)
        ])
        
        if explanation_level == "simple":
            prompt = f"""
You are helping a 14-year-old understand a tender document.
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