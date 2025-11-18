"""
Ingestion Workflow using LangGraph - Enhanced with Tender Details Extraction
"""
import re
import json
import logging
import concurrent.futures
from typing import List
from io import BytesIO
import requests
import PyPDF2
from rank_bm25 import BM25Okapi
from langgraph.graph import StateGraph, END

from workflows.workflow_states import TenderIngestionState
from services.embedding_service import EmbeddingService
from repositories.tender_project_repository import TenderProjectRepository
from repositories.tender_file_repository import TenderFileRepository
from repositories.tender_chunk_repository import TenderChunkRepository
from core.domain_models import TenderProject, TenderFile, TenderChunk
from utils.text_processing import preprocess_text
from config.settings import settings
from config.model_config import model_config

logger = logging.getLogger(__name__)

# Initialize services and repositories
embedding_service = EmbeddingService()
project_repo = TenderProjectRepository()
file_repo = TenderFileRepository()
chunk_repo = TenderChunkRepository()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_project_value_from_text(text: str) -> str:
    """
    Try to extract project value using regex patterns
    Looks for common patterns like "Total Estimated Cost", "Project Cost", etc.
    """
    patterns = [
        r'Total\s+Estimated\s+Cost[:\s]+(?:Rs\.?|₹)\s*([\d,\.]+)',
        r'Project\s+Cost[:\s]+(?:Rs\.?|₹)\s*([\d,\.]+)',
        r'Estimated\s+Amount[:\s]+(?:Rs\.?|₹)\s*([\d,\.]+)',
        r'Contract\s+Value[:\s]+(?:Rs\.?|₹)\s*([\d,\.]+)',
        r'Total\s+Value[:\s]+(?:Rs\.?|₹)\s*([\d,\.]+)',
        r'Tender\s+Value[:\s]+(?:Rs\.?|₹)\s*([\d,\.]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1)
            logger.debug(f"Found project value using pattern: {pattern[:30]}... -> {value}")
            return f"Rs. {value}"
    
    return None


def clean_currency_value(value: str) -> float:
    """
    Convert currency string to float value
    Examples:
        "₹6,54,780" -> 654780.0
        "$1,000,000" -> 1000000.0
        "50,00,000" -> 5000000.0
    """
    if not value or value in ["null", "None", "N/A", "Not found", "Not specified"]:
        return 0.0
    
    try:
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[₹$€£,\s]', '', str(value))
        # Convert to float
        return float(cleaned)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert currency value: {value}")
        return 0.0


def parse_date(date_str: str) -> str:
    """
    Ensure date is in proper format or return None
    """
    if not date_str or date_str in ["null", "None", "N/A", "Not found", "Not specified"]:
        return None
    
    # If already in correct format, return as-is
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return date_str
    
    return None


def parse_datetime(datetime_str: str) -> str:
    """
    Ensure datetime is in proper format or return None
    """
    if not datetime_str or datetime_str in ["null", "None", "N/A", "Not found", "Not specified"]:
        return None
    
    # If already in correct format, return as-is
    if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', datetime_str):
        return datetime_str
    
    return None


# ============================================================================
# WORKFLOW NODES
# ============================================================================

def fetch_pdf_from_url(state: TenderIngestionState) -> TenderIngestionState:
    """Download PDF and extract text"""
    try:
        logger.info(f"Fetching PDF from: {state['file_url']}")
        
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
        
        logger.info(f"Extracted {len(raw_text)} characters from {len(pdf_reader.pages)} pages")
        
    except Exception as e:
        state['error'] = f"PDF fetch error: {str(e)}"
        logger.error(state['error'])
    
    return state


def extract_tender_details(state: TenderIngestionState) -> TenderIngestionState:
    """Extract detailed tender information using LLM"""
    if state.get('error'):
        return state
    
    try:
        logger.info("Extracting tender details from document")
        
        # Use more text for better extraction (first 25000 characters)
        raw_text = state['raw_text'][:25000]
        
        prompt = f"""
Analyze this tender document carefully and extract the following information.
Respond ONLY with valid JSON containing these exact fields:

{{
    "tender_id": "Extract the unique tender ID/number/reference from the document",
    "project_title": "Extract the project name/title",
    "issuing_authority": "Extract the organization/department issuing this tender",
    "location": "Extract the project location/site",
    "project_value": "Extract the TOTAL ESTIMATED PROJECT COST/VALUE with currency symbol (NOT the EMD amount)",
    "emd_amount": "Extract the EMD/Earnest Money Deposit amount with currency symbol",
    "summary": "Write a brief 1-2 line summary of what this project is about",
    "tender_date": "Extract tender issue date in YYYY-MM-DD format if available",
    "submission_deadline": "Extract submission deadline in YYYY-MM-DDTHH:MM:SSZ format if available"
}}

CRITICAL INSTRUCTIONS:
- For project_value: Look for terms like "Total Estimated Cost", "Project Cost", "Contract Value", "Estimated Amount", "Total Value"
  This should be the LARGEST amount in the document (NOT the EMD/Earnest Money Deposit)
  Include currency symbol in the value (e.g., "Rs. 1,49,81,795.00" or "₹1,49,81,795")
- For emd_amount: Look for "EMD", "Earnest Money", "Bid Security" - this is usually a smaller amount
  Include currency symbol (e.g., "Rs. 2,99,636/-")
- The project_value should typically be much larger than emd_amount (often 10-100x larger)
- If a field is not found, use null
- For dates, use exact formats specified
- Summary should be concise (1-2 lines max)
- Respond ONLY with the JSON object, no other text

Document content:
{raw_text}

JSON:
"""
        
        model = model_config.get_summary_model()
        response = model.generate_content(prompt)
        
        logger.debug(f"LLM Response: {response.text[:500]}")
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            tender_details = json.loads(json_match.group(0))
            
            # Clean up null strings to actual None
            for key, value in tender_details.items():
                if value in ["null", "None", "N/A", "Not found", "Not specified", ""]:
                    tender_details[key] = None
            
            # Get project_value and emd_amount
            project_value_raw = tender_details.get('project_value')
            emd_amount_raw = tender_details.get('emd_amount')
            
            # Convert project_value to numeric for database
            project_value_numeric = clean_currency_value(project_value_raw)
            
            # Parse dates
            tender_date = parse_date(tender_details.get('tender_date'))
            submission_deadline = parse_datetime(tender_details.get('submission_deadline'))
            
            # Validation: project_value should be larger than EMD
            if project_value_raw and emd_amount_raw:
                emd_numeric = clean_currency_value(emd_amount_raw)
                if emd_numeric > project_value_numeric and project_value_numeric > 0:
                    logger.warning(f"⚠️  Detected potential swap: EMD ({emd_amount_raw}) > Project Value ({project_value_raw})")
                    logger.warning("⚠️  Attempting to find correct project value using regex...")
                    
                    # Try to extract using regex patterns
                    regex_value = extract_project_value_from_text(raw_text)
                    if regex_value:
                        logger.info(f"✓ Found project value using regex: {regex_value}")
                        project_value_raw = regex_value
                        project_value_numeric = clean_currency_value(regex_value)
                    else:
                        logger.warning("⚠️  Could not find better value, swapping LLM extracted values")
                        # Swap them as last resort
                        project_value_raw, emd_amount_raw = emd_amount_raw, project_value_raw
                        project_value_numeric = clean_currency_value(project_value_raw)
            
            # If project value is still too small, try regex extraction
            if project_value_numeric < 100000:  # Less than 1 lakh seems too small for a project
                logger.warning(f"⚠️  Project value seems too small: {project_value_numeric}")
                regex_value = extract_project_value_from_text(raw_text)
                if regex_value:
                    regex_numeric = clean_currency_value(regex_value)
                    if regex_numeric > project_value_numeric:
                        logger.info(f"✓ Using regex-extracted value: {regex_value} instead of {project_value_raw}")
                        project_value_raw = regex_value
                        project_value_numeric = regex_numeric
            
            # Store extracted details for API response (with formatting)
            state['extracted_tender_details'] = {
                "tender_id": tender_details.get('tender_id'),
                "project_title": tender_details.get('project_title'),
                "issuing_authority": tender_details.get('issuing_authority'),
                "location": tender_details.get('location'),
                "project_value": project_value_raw,  # Keep formatted for display
                "emd_amount": emd_amount_raw,
                "summary": tender_details.get('summary')
            }
            
            # Store structured data for database (with numeric values)
            state['structured_data'] = {
                "file_name": tender_details.get('project_title', 'Tender Document'),
                "tender_date": tender_date,
                "submission_deadline": submission_deadline,
                "tender_status": "Open",
                "tender_value": project_value_numeric,  # Numeric value for DB
            }
            
            logger.info(f"✓ Extracted tender details:")
            logger.info(f"  Tender ID: {tender_details.get('tender_id', 'N/A')}")
            logger.info(f"  Project Title: {tender_details.get('project_title', 'N/A')}")
            logger.info(f"  Issuing Authority: {tender_details.get('issuing_authority', 'N/A')}")
            logger.info(f"  Location: {tender_details.get('location', 'N/A')}")
            logger.info(f"  Project Value: {project_value_raw} (DB: {project_value_numeric})")
            logger.info(f"  EMD Amount: {emd_amount_raw}")
            logger.info(f"  Summary: {tender_details.get('summary', 'N/A')[:100]}...")
            
        else:
            logger.warning("Could not extract JSON from LLM response")
            state['extracted_tender_details'] = {
                "tender_id": None,
                "project_title": None,
                "issuing_authority": None,
                "location": None,
                "project_value": None,
                "emd_amount": None,
                "summary": None
            }
            state['structured_data'] = {
                "file_name": "Tender Document",
                "tender_value": 0.0
            }
            
    except Exception as e:
        logger.error(f"Tender details extraction error: {e}", exc_info=True)
        state['extracted_tender_details'] = {
            "tender_id": None,
            "project_title": None,
            "issuing_authority": None,
            "location": None,
            "project_value": None,
            "emd_amount": None,
            "summary": None
        }
        state['structured_data'] = {
            "file_name": "Tender Document",
            "tender_value": 0.0
        }
    
    return state


def chunk_document(state: TenderIngestionState) -> TenderIngestionState:
    """Split document into chunks"""
    if state.get('error'):
        return state
    
    try:
        logger.info("Chunking document")
        
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
        logger.info(f"Created {len(chunks)} chunks")
        
    except Exception as e:
        state['error'] = f"Chunking error: {str(e)}"
        logger.error(state['error'])
    
    return state


def generate_hybrid_embeddings(state: TenderIngestionState) -> TenderIngestionState:
    """Generate dense and sparse embeddings in parallel"""
    if state.get('error') or not state.get('chunks'):
        return state
    
    try:
        logger.info("Generating embeddings")
        
        chunks = state['chunks']
        chunk_texts = [chunk['text'] for chunk in chunks]
        
        # Dense embeddings (parallel)
        logger.debug(f"Generating dense embeddings using {settings.MAX_PARALLEL_WORKERS} workers")
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_PARALLEL_WORKERS) as executor:
            dense_embeddings = list(executor.map(
                lambda text: embedding_service.generate_dense_embedding(text, "retrieval_document"),
                chunk_texts
            ))
        
        # Sparse embeddings (parallel tokenization)
        logger.debug("Generating sparse embeddings")
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
        logger.info(f"Generated {len(hybrid_embeddings)} hybrid embeddings")
        
    except Exception as e:
        state['error'] = f"Embedding error: {str(e)}"
        logger.error(state['error'])
    
    return state


def store_in_database(state: TenderIngestionState) -> TenderIngestionState:
    """Store everything in database using repositories"""
    if state.get('error'):
        return state
    
    try:
        logger.info("Storing data in database")
        
        data = state.get('structured_data', {})
        
        # Create project
        project = TenderProject(
            project_id=state['project_id'],
            tender_number=state.get('tender_number', 'N/A'),
            tender_date=data.get('tender_date'),
            submission_deadline=data.get('submission_deadline'),
            tender_status=data.get('tender_status', 'Open'),
            tender_value=data.get('tender_value', 0.0)
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
        logger.info(f"✓ Successfully stored data: File ID {tender_file_id}, {len(db_chunks)} chunks")
        
    except Exception as e:
        state['error'] = f"Database error: {str(e)}"
        logger.error(state['error'], exc_info=True)
    
    return state


# ============================================================================
# BUILD WORKFLOW
# ============================================================================

logger.info("Building ingestion workflow")
workflow = StateGraph(TenderIngestionState)

workflow.add_node("fetch_pdf", fetch_pdf_from_url)
workflow.add_node("extract_details", extract_tender_details)
workflow.add_node("chunk_document", chunk_document)
workflow.add_node("generate_embeddings", generate_hybrid_embeddings)
workflow.add_node("store_in_db", store_in_database)

workflow.set_entry_point("fetch_pdf")
workflow.add_edge("fetch_pdf", "extract_details")
workflow.add_edge("extract_details", "chunk_document")
workflow.add_edge("chunk_document", "generate_embeddings")
workflow.add_edge("generate_embeddings", "store_in_db")
workflow.add_edge("store_in_db", END)

ingestion_app = workflow.compile()
logger.info("Ingestion workflow compiled successfully")