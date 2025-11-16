#database/models.py
"""
SQLAlchemy ORM Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, Text, ForeignKey, Date, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class TenderProject(Base):
    """Tender Project Model"""
    __tablename__ = 'tender_projects'
    
    tender_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, unique=True, nullable=False)
    tender_number = Column(String(100))
    tender_date = Column(Date)
    submission_deadline = Column(DateTime(timezone=True))
    tender_status = Column(String(50), default='Open')
    tender_value = Column(Numeric(18, 2), default=0.00)
    created_by = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_by = Column(Text)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    files = relationship("TenderFile", back_populates="project", cascade="all, delete-orphan")


class TenderFile(Base):
    """Tender File Model"""
    __tablename__ = 'tender_files'
    
    tender_file_id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(Integer, ForeignKey('tender_projects.tender_id', ondelete='CASCADE'), nullable=False)
    file_name = Column(Text, nullable=False)
    file_path = Column(Text)
    file_type = Column(String(20), default='pdf')
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_by = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_by = Column(Text)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    summary = Column(Text)
    simple_summary = Column(Text)
    bm25_corpus = Column(JSONB)
    
    # Relationships
    project = relationship("TenderProject", back_populates="files")
    chunks = relationship("TenderChunk", back_populates="file", cascade="all, delete-orphan")


class TenderChunk(Base):
    """Tender Chunk Model"""
    __tablename__ = 'tender_chunks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_file_id = Column(Integer, ForeignKey('tender_files.tender_file_id', ondelete='CASCADE'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_metadata = Column(JSONB)
    dense_embedding = Column(Vector(768))
    sparse_embedding = Column(JSONB)
    bm25_tokens = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    file = relationship("TenderFile", back_populates="chunks")
