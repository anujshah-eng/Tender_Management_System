#database/connection.py
"""
Database Connection Management with SQLAlchemy
"""
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections and session pooling"""
    
    _engine = None
    _session_factory = None
    
    @classmethod
    def initialize_pool(cls):
        """Initialize connection pool"""
        if cls._engine is not None:
            logger.warning("Database pool already initialized")
            return
        
        logger.info("Initializing database connection pool")
        logger.debug(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
        logger.debug(f"Database: {settings.DB_NAME}")
        logger.debug(f"User: {settings.DB_USER}")
        
        database_url = (
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        
        cls._engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False  # Set to True for SQL query logging
        )
        
        cls._session_factory = sessionmaker(
            bind=cls._engine,
            autocommit=False,
            autoflush=False
        )
        
        logger.info("Database connection pool initialized successfully")
        logger.debug(f"Pool size: 10, Max overflow: 20")
    
    @classmethod
    def get_session(cls) -> Session:
        """Get a database session"""
        if cls._session_factory is None:
            logger.error("Database pool not initialized")
            raise RuntimeError("Database pool not initialized. Call initialize_pool() first")
        
        logger.debug("Creating new database session")
        return cls._session_factory()
    
    @classmethod
    def close_all_connections(cls):
        """Close all database connections"""
        if cls._engine:
            logger.info("Closing all database connections")
            cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info("All database connections closed")


@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic commit/rollback"""
    session = DatabaseConnection.get_session()
    logger.debug(f"Session opened: {id(session)}")
    
    try:
        yield session
        session.commit()
        logger.debug(f"Session committed: {id(session)}")
    except Exception as e:
        session.rollback()
        logger.error(f"Session rolled back due to error: {e}", exc_info=True)
        raise
    finally:
        session.close()
        logger.debug(f"Session closed: {id(session)}")