# repositories/tender_project_repository.py
"""
TenderProject Repository with SQLAlchemy
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from repositories.base_repository import BaseRepository
from database.models import TenderProject
from core.interfaces import ITenderProjectRepository
from core.domain_models import TenderProject as DomainTenderProject
from database.connection import get_db_session

logger = logging.getLogger(__name__)


class TenderProjectRepository(BaseRepository[TenderProject], ITenderProjectRepository):
    """Repository for TenderProject operations"""
    
    def __init__(self):
        super().__init__(TenderProject)
        logger.debug("TenderProjectRepository initialized")
    
    def create(self, project: DomainTenderProject) -> int:
        """Create a new tender project"""
        logger.info(f"Creating tender project: {project.tender_number}")
        logger.debug(f"Project ID: {project.project_id}, Status: {project.tender_status}")
        
        with get_db_session() as db:
            # Check if project exists
            existing = db.query(TenderProject).filter(
                TenderProject.project_id == project.project_id
            ).first()
            
            if existing:
                logger.info(f"Project already exists with tender_id={existing.tender_id}, updating...")
                existing.tender_number = project.tender_number
                existing.tender_date = project.tender_date
                existing.submission_deadline = project.submission_deadline
                existing.tender_status = project.tender_status
                existing.tender_value = project.tender_value
                db.flush()
                logger.info(f"Updated existing project: tender_id={existing.tender_id}")
                return existing.tender_id
            else:
                logger.debug("Creating new project record...")
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
                logger.info(f"Created new project with tender_id={new_project.tender_id}")
                return new_project.tender_id
    
    def get_by_id(self, tender_id: int) -> Optional[DomainTenderProject]:
        """Get project by ID"""
        logger.debug(f"Fetching tender project: tender_id={tender_id}")
        
        with get_db_session() as db:
            project = db.query(TenderProject).filter(
                TenderProject.tender_id == tender_id
            ).first()
            
            if not project:
                logger.warning(f"Tender project not found: tender_id={tender_id}")
                return None
            
            logger.debug(f"Found tender project: {project.tender_number}")
            
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
        logger.info(f"Updating tender project: tender_id={project.tender_id}")
        logger.debug(f"Status: {project.tender_status}, Value: {project.tender_value}")
        
        with get_db_session() as db:
            db_project = db.query(TenderProject).filter(
                TenderProject.tender_id == project.tender_id
            ).first()
            
            if db_project:
                db_project.tender_status = project.tender_status
                db_project.tender_value = project.tender_value
                db_project.updated_by = project.updated_by
                db.flush()
                logger.info("Project updated successfully")
                return True
            
            logger.warning(f"Project not found for update: tender_id={project.tender_id}")
            return False