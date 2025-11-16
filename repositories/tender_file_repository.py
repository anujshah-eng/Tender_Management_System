# repositories/tender_file_repository.py
"""
TenderFile Repository with SQLAlchemy
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from repositories.base_repository import BaseRepository
from database.models import TenderFile
from core.interfaces import ITenderFileRepository
from core.domain_models import TenderFile as DomainTenderFile # Add this line
from database.connection import get_db_session 


class TenderFileRepository(BaseRepository[TenderFile], ITenderFileRepository):
    """Repository for TenderFile operations"""
    
    def __init__(self):
        super().__init__(TenderFile)
    
    def create(self, file: DomainTenderFile) -> int:
        """Create a new tender file"""
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
            return new_file.tender_file_id
    
    def get_by_id(self, tender_file_id: int) -> Optional[DomainTenderFile]:
        """Get file by ID"""
        with get_db_session() as db:
            file = db.query(TenderFile).filter(
                TenderFile.tender_file_id == tender_file_id
            ).first()
            
            if not file:
                return None
            
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
        with get_db_session() as db:
            file = db.query(TenderFile).filter(
                TenderFile.tender_file_id == tender_file_id
            ).first()
            
            if file:
                file.summary = summary
                file.simple_summary = simple_summary
                db.flush()
                return True
            return False
    
    def exists(self, tender_file_id: int) -> bool:
        """Check if file exists"""
        with get_db_session() as db:
            return db.query(TenderFile).filter(
                TenderFile.tender_file_id == tender_file_id
            ).first() is not None

