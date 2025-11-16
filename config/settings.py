"""
Application Settings and Configuration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Find and load .env file
# Try multiple locations
env_locations = [
    Path.cwd() / ".env",  # Current directory
    Path(__file__).parent.parent / ".env",  # Project root
    Path(__file__).parent.parent.parent / ".env",  # One level up
]

env_loaded = False
for env_path in env_locations:
    if env_path.exists():
        print(f"✓ Loading .env from: {env_path}")
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    print("⚠️  WARNING: .env file not found in any of these locations:")
    for path in env_locations:
        print(f"  - {path}")


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    APP_NAME: str = "Tender Management System"
    APP_VERSION: str = "2.0.0"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    
    # Google AI
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_NAME: str = os.getenv("DB_NAME", "tender_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    
    # Processing Parameters
    MAX_CHUNK_SIZE: int = int(os.getenv("MAX_CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    HYBRID_SEARCH_ALPHA: float = float(os.getenv("HYBRID_SEARCH_ALPHA", "0.7"))
    TOP_K_CHUNKS: int = int(os.getenv("TOP_K_CHUNKS", "5"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    MAX_PARALLEL_WORKERS: int = int(os.getenv("MAX_PARALLEL_WORKERS", "5"))
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Validation (skip for database setup scripts)
is_setup_script = any(x in sys.argv[0].lower() for x in ['setup', 'setup_db'])

if not is_setup_script:
    # Only validate if not running setup
    if not settings.GOOGLE_API_KEY:
        print("\n" + "="*70)
        print("❌ ERROR: GOOGLE_API_KEY not configured")
        print("="*70)
        print("\nThe application cannot start without a Google AI API key.")
        print("\nSteps to fix:")
        print("1. Get your API key from: https://makersuite.google.com/app/apikey")
        print("2. Create/edit .env file in project root")
        print("3. Add line: GOOGLE_API_KEY=your_actual_key_here")
        print("4. Save the file and restart")
        print("\nExample .env file:")
        print("-" * 50)
        print("GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        print("DB_HOST=localhost")
        print("DB_NAME=tender_db")
        print("DB_USER=postgres")
        print("DB_PASSWORD=your_password")
        print("DB_PORT=5432")
        print("-" * 50)
        print()
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    if not settings.DB_PASSWORD:
        print("\n⚠️  WARNING: DB_PASSWORD not set in .env file")
        print("Database operations may fail if authentication is required.\n")