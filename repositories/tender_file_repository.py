# repositories/tender_file_repository.py
"""
TenderFile Repository with SQLAlchemy
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from repositories.base_repository import BaseRepository
from database.models import TenderFile
from core.interfaces import ITenderFileRepository
from core.domain_models import TenderFile as DomainTenderFile
from database.connection import get_db_session

logger = logging.getLogger(__name__)


class TenderFileRepository(BaseRepository[TenderFile], ITenderFileRepository):
    """Repository for TenderFile operations"""
    
    def __init__(self):
        super().__init__(TenderFile)
        logger.debug("TenderFileRepository initialized")
    
    def create(self, file: DomainTenderFile) -> int:
        """Create a new tender file"""
        logger.info(f"Creating tender file: {file.file_name}")
        logger.debug(f"Tender ID: {file.tender_id}, File path: {file.file_path}")
        
        with get_db_session() as db:
            new_file = TenderFile(
                tender_id=file.tender_id,
                file_name=file.file_name,
                file_path=file.file_path,
                file_type=file.file_type,
                version=file.version,
                is_active=file.is_active,
                created_by=file.created_by,
                bm25_corpus=file.bm25_corpus
            )
            db.add(new_file)
            db.flush()
            db.refresh(new_file)
            
            logger.info(f"Created tender file with ID: {new_file.tender_file_id}")
            return new_file.tender_file_id
    
    def get_by_id(self, tender_file_id: int) -> Optional[DomainTenderFile]:
        """Get file by ID"""
        logger.debug(f"Fetching tender file: tender_file_id={tender_file_id}")
        
        with get_db_session() as db:
            file = db.query(TenderFile).filter(
                TenderFile.tender_file_id == tender_file_id
            ).first()
            
            if not file:
                logger.warning(f"Tender file not found: tender_file_id={tender_file_id}")
                return None
            
            logger.debug(f"Found tender file: {file.file_name}")
            
            return DomainTenderFile(
                tender_file_id=file.tender_file_id,
                tender_id=file.tender_id,
                file_name=file.file_name,
                file_path=file.file_path,
                file_type=file.file_type,
                version=file.version,
                is_active=file.is_active,
                created_by=file.created_by,
                created_at=file.created_at,
                updated_by=file.updated_by,
                updated_at=file.updated_at,
                summary=file.summary,
                simple_summary=file.simple_summary,
                bm25_corpus=file.bm25_corpus
            )
    
    def update_summary(self, tender_file_id: int, summary: str, simple_summary: str) -> bool:
        """Update file summaries"""
        logger.info(f"Updating summaries for tender_file_id={tender_file_id}")
        logger.debug(f"Summary length: {len(summary)}, Simple summary length: {len(simple_summary)}")
        
        with get_db_session() as db:
            file = db.query(TenderFile).filter(
                TenderFile.tender_file_id == tender_file_id
            ).first()
            
            if file:
                file.summary = summary
                file.simple_summary = simple_summary
                db.flush()
                logger.info("Summaries updated successfully")
                return True
            
            logger.warning(f"File not found for summary update: tender_file_id={tender_file_id}")
            return False
    
    def exists(self, tender_file_id: int) -> bool:
        """Check if file exists"""
        logger.debug(f"Checking if tender file exists: tender_file_id={tender_file_id}")
        
        with get_db_session() as db:
            exists = db.query(TenderFile).filter(
                TenderFile.tender_file_id == tender_file_id
            ).first() is not None
            
            logger.debug(f"Tender file exists: {exists}")
            return exists