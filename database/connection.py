#database/connection.py
"""
Database Connection Management with SQLAlchemy
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from config.settings import settings
from core.exceptions import DatabaseOperationException
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections with SQLAlchemy"""
    
    _engine = None
    _SessionLocal = None
    
    @classmethod
    def initialize_pool(cls):
        """Initialize SQLAlchemy engine and session factory"""
        if cls._engine is None:
            try:
                # Create database URL
                database_url = (
                    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
                    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
                )
                
                # Create engine with connection pooling
                cls._engine = create_engine(
                    database_url,
                    poolclass=QueuePool,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,  # Verify connections before using
                    echo=False  # Set to True for SQL logging
                )
                
                # Create session factory
                cls._SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=cls._engine
                )
                
                logger.info("✓ SQLAlchemy engine initialized")
                
            except Exception as e:
                raise DatabaseOperationException(f"Failed to initialize SQLAlchemy: {e}")
    
    @classmethod
    def get_session(cls) -> Session:
        """Get a new database session"""
        if cls._SessionLocal is None:
            cls.initialize_pool()
        return cls._SessionLocal()
    
    @classmethod
    def close_all_connections(cls):
        """Close all database connections"""
        if cls._engine:
            cls._engine.dispose()
            cls._engine = None
            cls._SessionLocal = None
            logger.info("✓ All database connections closed")


@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = DatabaseConnection.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise DatabaseOperationException(f"Database operation failed: {e}")
    finally:
        session.close()


# Dependency for FastAPI
def get_db():
    """FastAPI dependency for database sessions"""
    db = DatabaseConnection.get_session()
    try:
        yield db
    finally:
        db.close()