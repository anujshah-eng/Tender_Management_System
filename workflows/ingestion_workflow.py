"""
Ingestion Workflow using LangGraph
Adapted to Onion Architecture with Fixed Imports
"""
import re
import json
import concurrent.futures
from typing import List
from io import BytesIO
import requests
import PyPDF2
from rank_bm25 import BM25Okapi
from langgraph.graph import StateGraph, END

from workflows.workflow_states import TenderIngestionState  # Changed to relative import
from services.embedding_service import EmbeddingService  # Changed to relative import
from repositories.tender_project_repository import TenderProjectRepository  # Changed to relative import
from repositories.tender_file_repository import TenderFileRepository  # Changed to relative import
from repositories.tender_chunk_repository import TenderChunkRepository  # Changed to relative import
from core.domain_models import TenderProject, TenderFile, TenderChunk  # Changed to relative import
from utils.text_processing import preprocess_text  # Changed to relative import
from config.settings import settings  # Changed to relative import
from config.model_config import model_config  # Changed to relative import


# Initialize services and repositories
embedding_service = EmbeddingService()
project_repo = TenderProjectRepository()
file_repo = TenderFileRepository()
chunk_repo = TenderChunkRepository()


# ============================================================================
# WORKFLOW NODES
# ============================================================================

def fetch_pdf_from_url(state: TenderIngestionState) -> TenderIngestionState:
    """Download PDF and extract text"""
    try:
        print(f"📥 Fetching PDF from: {state['file_url']}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(state['file_url'], timeout=30, headers=headers, verify=False)
        response.raise_for_status()
        
        pdf_file = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        raw_text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                raw_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
        
        raw_text = re.sub(r'(\n\s*)+\n', '\n', raw_text)
        state['raw_text'] = raw_text
        state['error'] = ""
        
        print(f"✓ Extracted {len(raw_text)} characters from {len(pdf_reader.pages)} pages")
        
    except Exception as e:
        state['error'] = f"PDF fetch error: {str(e)}"
        print(f"❌ {state['error']}")
    
    return state


def structure_document(state: TenderIngestionState) -> TenderIngestionState:
    """Extract structured metadata using LLM"""
    if state.get('error'):
        return state
    
    try:
        print("🤖 Extracting structured data...")
        
        raw_text = state['raw_text'][:8000]  # Limit context
        
        prompt = f"""
Analyze this tender document and extract structured information.
Respond ONLY with valid JSON.

Fields:
- "file_name": Document title
- "tender_date": Date issued (YYYY-MM-DD)
- "submission_deadline": Deadline (YYYY-MM-DDTHH:MM:SSZ)
- "tender_status": Status ("Open"/"Closed")
- "tender_value": Estimated value (number)

Document:
{raw_text}

JSON:
"""
        
        model = model_config.get_summary_model()
        response = model.generate_content(prompt)
        
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            state['structured_data'] = data
            print(f"✓ Extracted: {data.get('file_name', 'Untitled')}")
        else:
            state['structured_data'] = {"file_name": "Tender Document"}
            
    except Exception as e:
        print(f"⚠️ Structure extraction warning: {e}")
        state['structured_data'] = {"file_name": "Tender Document"}
    
    return state


def chunk_document(state: TenderIngestionState) -> TenderIngestionState:
    """Split document into chunks"""
    if state.get('error'):
        return state
    
    try:
        print("✂️ Chunking document...")
        
        raw_text = state['raw_text']
        paragraphs = re.split(r'\n\s*\n', raw_text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) + 1 > settings.MAX_CHUNK_SIZE and current_chunk:
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": current_chunk.strip(),
                    "metadata": {"chunk_size": len(current_chunk), "source": state['file_url']}
                })
                current_chunk = ""
                chunk_index += 1
            
            current_chunk += para + "\n\n"
        
        if current_chunk.strip():
            chunks.append({
                "chunk_index": chunk_index,
                "text": current_chunk.strip(),
                "metadata": {"chunk_size": len(current_chunk), "source": state['file_url']}
            })
        
        state['chunks'] = chunks
        print(f"✓ Created {len(chunks)} chunks")
        
    except Exception as e:
        state['error'] = f"Chunking error: {str(e)}"
        print(f"❌ {state['error']}")
    
    return state


def generate_hybrid_embeddings(state: TenderIngestionState) -> TenderIngestionState:
    """Generate dense and sparse embeddings in parallel"""
    if state.get('error') or not state.get('chunks'):
        return state
    
    try:
        print("⚡ Generating embeddings...")
        
        chunks = state['chunks']
        chunk_texts = [chunk['text'] for chunk in chunks]
        
        # Dense embeddings (parallel)
        print(f"  → Dense embeddings ({settings.MAX_PARALLEL_WORKERS} workers)")
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_PARALLEL_WORKERS) as executor:
            dense_embeddings = list(executor.map(
                lambda text: embedding_service.generate_dense_embedding(text, "retrieval_document"),
                chunk_texts
            ))
        
        # Sparse embeddings (parallel tokenization)
        print(f"  → Sparse embeddings")
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_PARALLEL_WORKERS) as executor:
            tokenized_chunks = list(executor.map(preprocess_text, chunk_texts))
        
        sparse_embeddings = [
            embedding_service.generate_sparse_embedding(tokens)
            for tokens in tokenized_chunks
        ]
        
        # BM25 corpus stats
        if tokenized_chunks and any(len(t) > 0 for t in tokenized_chunks):
            bm25 = BM25Okapi(tokenized_chunks)
            if 'structured_data' not in state:
                state['structured_data'] = {}
            state['structured_data']['bm25_corpus'] = {
                'avg_doc_len': bm25.avgdl,
                'doc_lens': bm25.doc_len,
            }
        
        # Combine embeddings
        hybrid_embeddings = []
        for i, (dense, sparse, tokens) in enumerate(zip(dense_embeddings, sparse_embeddings, tokenized_chunks)):
            hybrid_embeddings.append({
                'chunk_index': i,
                'dense': dense,
                'sparse': sparse,
                'tokens': tokens
            })
        
        state['hybrid_embeddings'] = hybrid_embeddings
        print(f"✓ Generated {len(hybrid_embeddings)} hybrid embeddings")
        
    except Exception as e:
        state['error'] = f"Embedding error: {str(e)}"
        print(f"❌ {state['error']}")
    
    return state


def store_in_database(state: TenderIngestionState) -> TenderIngestionState:
    """Store everything in database using repositories"""
    if state.get('error'):
        return state
    
    try:
        print("💾 Storing in database...")
        
        data = state.get('structured_data', {})
        
        # Create project
        project = TenderProject(
            project_id=state['project_id'],
            tender_number=state.get('tender_number', 'N/A'),
            tender_date=data.get('tender_date'),
            submission_deadline=data.get('submission_deadline'),
            tender_status=data.get('tender_status', 'Open'),
            tender_value=data.get('tender_value', 0.00)
        )
        tender_id = project_repo.create(project)
        state['tender_id'] = tender_id
        
        # Create file
        file = TenderFile(
            tender_id=tender_id,
            file_name=data.get('file_name', 'Untitled'),
            file_path=state['file_url'],
            file_type='pdf',
            bm25_corpus=data.get('bm25_corpus', {})
        )
        tender_file_id = file_repo.create(file)
        state['tender_file_id'] = tender_file_id
        
        # Create chunks
        db_chunks = []
        for chunk, hybrid_emb in zip(state.get('chunks', []), state.get('hybrid_embeddings', [])):
            db_chunk = TenderChunk(
                tender_file_id=tender_file_id,
                chunk_index=chunk['chunk_index'],
                chunk_text=chunk['text'],
                chunk_metadata=chunk['metadata'],
                dense_embedding=hybrid_emb.get('dense', []),
                sparse_embedding=hybrid_emb.get('sparse', {}),
                bm25_tokens=hybrid_emb.get('tokens', [])
            )
            db_chunks.append(db_chunk)
        
        chunk_repo.bulk_create(db_chunks)
        
        state['db_status'] = f"Success: File ID {tender_file_id}, {len(db_chunks)} chunks"
        print(f"✓ {state['db_status']}")
        
    except Exception as e:
        state['error'] = f"Database error: {str(e)}"
        print(f"❌ {state['error']}")
    
    return state


# ============================================================================
# BUILD WORKFLOW
# ============================================================================

print("📊 Building ingestion workflow...")
workflow = StateGraph(TenderIngestionState)

workflow.add_node("fetch_pdf", fetch_pdf_from_url)
workflow.add_node("structure_document", structure_document)
workflow.add_node("chunk_document", chunk_document)
workflow.add_node("generate_embeddings", generate_hybrid_embeddings)
workflow.add_node("store_in_db", store_in_database)

workflow.set_entry_point("fetch_pdf")
workflow.add_edge("fetch_pdf", "structure_document")
workflow.add_edge("structure_document", "chunk_document")
workflow.add_edge("chunk_document", "generate_embeddings")
workflow.add_edge("generate_embeddings", "store_in_db")
workflow.add_edge("store_in_db", END)

ingestion_app = workflow.compile()
print("✓ Ingestion workflow compiled")