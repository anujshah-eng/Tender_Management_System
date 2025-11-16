# repositories/tender_project_repository.py
"""
TenderProject Repository with SQLAlchemy
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from repositories.base_repository import BaseRepository
from database.models import TenderProject # Changed to relative import
from core.interfaces import ITenderProjectRepository # Changed to relative import
from core.domain_models import TenderProject as DomainTenderProject # Changed to relative import
from database.connection import get_db_session



class TenderProjectRepository(BaseRepository[TenderProject], ITenderProjectRepository):
    """Repository for TenderProject operations"""
    
    def __init__(self):
        super().__init__(TenderProject)
    
    def create(self, project: DomainTenderProject) -> int:
        """Create a new tender project"""
        with get_db_session() as db:
            # Check if project exists
            existing = db.query(TenderProject).filter(
                TenderProject.project_id == project.project_id
            ).first()
            
            if existing:
                # Update existing
                existing.tender_number = project.tender_number
                existing.tender_date = project.tender_date
                existing.submission_deadline = project.submission_deadline
                existing.tender_status = project.tender_status
                existing.tender_value = project.tender_value
                db.flush()
                return existing.tender_id
            else:
                # Create new
                new_project = TenderProject(
                    project_id=project.project_id,
                    tender_number=project.tender_number,
                    tender_date=project.tender_date,
                    submission_deadline=project.submission_deadline,
                    tender_status=project.tender_status,
                    tender_value=project.tender_value,
                    created_by=project.created_by
                )
                db.add(new_project)
                db.flush()
                db.refresh(new_project)
                return new_project.tender_id
    
    def get_by_id(self, tender_id: int) -> Optional[DomainTenderProject]:
        """Get project by ID"""
        with get_db_session() as db:
            project = db.query(TenderProject).filter(
                TenderProject.tender_id == tender_id
            ).first()
            
            if not project:
                return None
            
            return DomainTenderProject(
                tender_id=project.tender_id,
                project_id=project.project_id,
                tender_number=project.tender_number,
                tender_date=project.tender_date,
                submission_deadline=project.submission_deadline,
                tender_status=project.tender_status,
                tender_value=project.tender_value,
                created_by=project.created_by,
                created_at=project.created_at,
                updated_by=project.updated_by,
                updated_at=project.updated_at
            )
    
    def update(self, project: DomainTenderProject) -> bool:
        """Update existing project"""
        with get_db_session() as db:
            db_project = db.query(TenderProject).filter(
                TenderProject.tender_id == project.tender_id
            ).first()
            
            if db_project:
                db_project.tender_status = project.tender_status
                db_project.tender_value = project.tender_value
                db_project.updated_by = project.updated_by
                db.flush()
                return True
            return False
