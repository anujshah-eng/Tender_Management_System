# config/settings.py
"""
Application Settings and Configuration
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import urllib3

# Configure logger
logger = logging.getLogger(__name__)

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Find and load .env file
env_locations = [
    Path.cwd() / ".env",
    Path(__file__).parent.parent / ".env",
    Path(__file__).parent.parent.parent / ".env",
]

env_loaded = False
for env_path in env_locations:
    if env_path.exists():
        logger.info(f"Loading .env from: {env_path}")
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    logger.warning("WARNING: .env file not found in any of these locations:")
    for path in env_locations:
        logger.warning(f"  - {path}")


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    APP_NAME: str = "Tender Management System"
    APP_VERSION: str = "2.0.0"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    
    # Google AI
    GOOGLE_API_KEY: str = ""
    
    # Database
    DB_HOST: str = "localhost"
    DB_NAME: str = "tender_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_PORT: int = 5432
    
    # Processing Parameters
    MAX_CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    HYBRID_SEARCH_ALPHA: float = 0.7
    TOP_K_CHUNKS: int = 5
    MAX_RETRIES: int = 3
    MAX_PARALLEL_WORKERS: int = 5
    
    # Embedding API Limits
    MAX_EMBEDDING_CHARS: int = 10000
    MAX_EMBEDDING_TOKENS: int = 2048
    
    # Model Settings
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    SUMMARY_MODEL: str = "models/gemini-2.5-flash"
    QA_MODEL: str = "models/gemini-2.5-flash"
    
    # Temperature settings
    SUMMARY_TEMPERATURE: float = 0.7
    QA_TEMPERATURE: float = 0.4
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'  # This allows extra fields in .env without errors
    )


# Global settings instance
settings = Settings()

# Validation (skip for database setup scripts)
is_setup_script = any(x in sys.argv[0].lower() for x in ['setup', 'setup_db'])

if not is_setup_script:
    if not settings.GOOGLE_API_KEY:
        logger.error("="*70)
        logger.error("ERROR: GOOGLE_API_KEY not configured")
        logger.error("="*70)
        logger.error("\nThe application cannot start without a Google AI API key.")
        logger.error("\nSteps to fix:")
        logger.error("1. Get your API key from: https://makersuite.google.com/app/apikey")
        logger.error("2. Create/edit .env file in project root")
        logger.error("3. Add line: GOOGLE_API_KEY=your_actual_key_here")
        logger.error("4. Save the file and restart")
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    if not settings.DB_PASSWORD:
        logger.warning("WARNING: DB_PASSWORD not set in .env file")
        logger.warning("Database operations may fail if authentication is required.\n")