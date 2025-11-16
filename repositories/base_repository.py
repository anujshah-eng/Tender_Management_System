# repositories/base_repository.py
"""
Base Repository with SQLAlchemy
"""
from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from database.connection import get_db_session
from database.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def create(self, db: Session, **kwargs) -> ModelType:
        """Create a new record"""
        instance = self.model(**kwargs)
        db.add(instance)
        db.flush()
        db.refresh(instance)
        return instance
    
    def get_by_id(self, db: Session, id: int) -> Optional[ModelType]:
        """Get record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination"""
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, db: Session, id: int, **kwargs) -> Optional[ModelType]:
        """Update a record"""
        instance = self.get_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            db.flush()
            db.refresh(instance)
        return instance
    
    def delete(self, db: Session, id: int) -> bool:
        """Delete a record"""
        instance = self.get_by_id(db, id)
        if instance:
            db.delete(instance)
            db.flush()
            return True
        return False

