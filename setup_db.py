#Setup_db.py
"""
Database Setup Script - Run from project root
Usage: python setup_db.py
"""
import sys
import os
from pathlib import Path

# Ensure we're in the project root
PROJECT_ROOT = Path(__file__).parent.absolute()
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

print("="*70)
print("DATABASE SETUP")
print("="*70)
print(f"Working directory: {os.getcwd()}")

# Load environment
from dotenv import load_dotenv
env_file = PROJECT_ROOT / ".env"

if not env_file.exists():
    print(f"\n❌ .env file not found at: {env_file}")
    print("\nCreate .env file with your configuration:")
    print("GOOGLE_API_KEY=your_key")
    print("DB_HOST=localhost")
    print("DB_NAME=tender_db")
    print("DB_USER=postgres")
    print("DB_PASSWORD=your_password")
    print("DB_PORT=5432")
    sys.exit(1)

load_dotenv(env_file)
print(f"✓ Loaded .env from: {env_file}")

# Now import and run setup
try:
    from sqlalchemy import create_engine, text
    from config.settings import settings
    from database.models import Base
    
    print("\n🔧 Creating database connection...")
    
    # Create database URL
    database_url = (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    
    # Create engine
    engine = create_engine(database_url, echo=False)
    
    print("✓ Connected to database")
    
    # Enable pgvector
    print("\n🔧 Enabling pgvector extension...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    print("✓ pgvector enabled")
    
    # Drop existing tables
    print("\n⚠️  Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ Dropped existing tables")
    
    # Create all tables
    print("\n📊 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Created tables")
    
    # Create indexes
    print("\n⚡ Creating indexes...")
    with engine.connect() as conn:
        # Dense embedding index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS tender_chunks_dense_embedding_idx 
            ON tender_chunks USING hnsw (dense_embedding vector_cosine_ops);
        """))
        
        # Sparse embedding index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS tender_chunks_sparse_embedding_idx 
            ON tender_chunks USING gin (sparse_embedding);
        """))
        
        # BM25 tokens index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS tender_chunks_bm25_tokens_idx 
            ON tender_chunks USING gin (bm25_tokens);
        """))
        
        # Foreign key indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS tender_files_tender_id_idx 
            ON tender_files(tender_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS tender_chunks_tender_file_id_idx 
            ON tender_chunks(tender_file_id);
        """))
        
        conn.commit()
    print("✓ Created indexes")
    
    # Verify
    print("\n✅ Verifying tables...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'tender%'
            ORDER BY table_name;
        """))
        tables = result.fetchall()
        for table in tables:
            print(f"  ✓ {table[0]}")
    
    engine.dispose()
    
    print("\n" + "="*70)
    print("✅ DATABASE SETUP COMPLETE!")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)