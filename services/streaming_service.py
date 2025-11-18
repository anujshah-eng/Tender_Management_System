# services/streaming_service.py
"""
SSE Streaming Service for Real-time Responses
"""
import json
import asyncio
import logging
from typing import AsyncGenerator
from core.interfaces import IStreamingService
from services.retrieval_service import RetrievalService
from config.model_config import model_config
from config.settings import settings
from core.exceptions import DocumentNotFoundException

logger = logging.getLogger(__name__)


class StreamingService(IStreamingService):
    """Handles SSE streaming for Q&A and Summary generation"""
    
    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval_service = retrieval_service
        logger.info("StreamingService initialized")
    
    async def stream_summary(
        self, 
        tender_file_id: int, 
        explanation_level: str
    ) -> AsyncGenerator[str, None]:
        """Stream summary generation with SSE"""
        logger.info("="*70)
        logger.info("STREAMING SUMMARY GENERATION")
        logger.info("="*70)
        logger.info(f"Tender File ID: {tender_file_id}")
        logger.info(f"Explanation Level: {explanation_level}")
        
        try:
            # Yield initial status
            yield self._create_sse_event("status", "Retrieving document chunks...")
            await asyncio.sleep(0.1)
            
            # Get all chunks
            logger.debug("Fetching all chunks...")
            chunks = self.retrieval_service.get_all_chunks(tender_file_id)
            
            if not chunks:
                logger.error(f"No chunks found for tender_file_id={tender_file_id}")
                raise DocumentNotFoundException(f"No chunks found for file {tender_file_id}")
            
            logger.info(f"Retrieved {len(chunks)} chunks")
            yield self._create_sse_event("status", f"Processing {len(chunks)} chunks...")
            await asyncio.sleep(0.1)
            
            # Prepare context
            logger.debug("Preparing context for LLM...")
            context = self._prepare_summary_context(chunks, explanation_level)
            logger.debug(f"Context prepared: {len(context)} characters")
            
            yield self._create_sse_event("status", "Generating summary...")
            await asyncio.sleep(0.1)
            
            # Get streaming model
            logger.debug(f"Loading model with temperature={settings.SUMMARY_TEMPERATURE}")
            model = model_config.get_streaming_model(
                temperature=settings.SUMMARY_TEMPERATURE
            )
            
            # Stream the response
            logger.info("Starting LLM streaming...")
            full_response = ""
            token_count = 0
            response = model.generate_content(context, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    token_count += 1
                    yield self._create_sse_event("token", chunk.text)
                    await asyncio.sleep(0.01)
            
            logger.info(f"Streaming complete: {token_count} tokens, {len(full_response)} chars")
            
            # Send completion
            yield self._create_sse_event("complete", full_response)
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield self._create_sse_event("error", str(e))
    
    async def stream_qa_response(
        self, 
        tender_file_id: int,
        question: str,
        explanation_level: str
    ) -> AsyncGenerator[str, None]:
        """Stream Q&A response with SSE"""
        logger.info("="*70)
        logger.info("STREAMING Q&A RESPONSE")
        logger.info("="*70)
        logger.info(f"Tender File ID: {tender_file_id}")
        logger.info(f"Question: {question}")
        logger.info(f"Explanation Level: {explanation_level}")
        
        try:
            # Yield initial status
            yield self._create_sse_event("status", "Searching relevant sections...")
            await asyncio.sleep(0.1)
            
            # Retrieve relevant chunks
            logger.debug("Retrieving relevant chunks...")
            search_results = self.retrieval_service.retrieve_relevant_chunks(
                tender_file_id=tender_file_id,
                query=question,
                top_k=settings.TOP_K_CHUNKS
            )
            
            if not search_results:
                logger.warning("No relevant information found")
                yield self._create_sse_event("error", "No relevant information found")
                return
            
            logger.info(f"Found {len(search_results)} relevant chunks")
            yield self._create_sse_event("status", f"Found {len(search_results)} relevant sections...")
            await asyncio.sleep(0.1)
            
            # Prepare context
            logger.debug("Preparing Q&A context...")
            context = self._prepare_qa_context(question, search_results, explanation_level)
            logger.debug(f"Context prepared: {len(context)} characters")
            
            yield self._create_sse_event("status", "Generating answer...")
            await asyncio.sleep(0.1)
            
            # Get streaming model
            logger.debug(f"Loading model with temperature={settings.QA_TEMPERATURE}")
            model = model_config.get_streaming_model(
                temperature=settings.QA_TEMPERATURE
            )
            
            # Stream the response
            logger.info("Starting LLM streaming...")
            full_response = ""
            token_count = 0
            response = model.generate_content(context, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    token_count += 1
                    yield self._create_sse_event("token", chunk.text)
                    await asyncio.sleep(0.01)
            
            logger.info(f"Streaming complete: {token_count} tokens, {len(full_response)} chars")
            
            # Send completion with metadata
            completion_data = {
                "answer": full_response,
                "chunks_used": len(search_results),
                "top_relevance": search_results[0].relevance_score if search_results else 0
            }
            yield self._create_sse_event("complete", json.dumps(completion_data))
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield self._create_sse_event("error", str(e))
    
    def _create_sse_event(self, event_type: str, data: str) -> str:
        """Create SSE formatted event"""
        logger.debug(f"SSE Event: {event_type} ({len(data)} chars)")
        return f"event: {event_type}\ndata: {data}\n\n"
    
    def _prepare_summary_context(self, chunks, explanation_level: str) -> str:
        """Prepare context for summary generation"""
        logger.debug(f"Preparing summary context with {len(chunks)} chunks, level={explanation_level}")
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
        logger.debug(f"Summary prompt prepared: {len(prompt)} characters")
        return prompt
    
    def _prepare_qa_context(self, question: str, search_results, explanation_level: str) -> str:
        """Prepare context for Q&A"""
        logger.debug(f"Preparing Q&A context with {len(search_results)} results, level={explanation_level}")
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
        logger.debug(f"Q&A prompt prepared: {len(prompt)} characters")
        return prompt