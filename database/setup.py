"""
Database Setup Module
This should be called from setup_db.py in project root, not run directly
"""
from sqlalchemy import text
from .models import Base
from .connection import DatabaseConnection
from ..config.settings import settings


def setup_database():
    """Create database tables using SQLAlchemy"""
    print("="*70)
    print("DATABASE SETUP WITH SQLALCHEMY")
    print("="*70)
    
    try:
        # Initialize connection
        DatabaseConnection.initialize_pool()
        engine = DatabaseConnection._engine
        
        # Enable pgvector extension
        print("\n🔧 Enabling pgvector extension...")
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
        print("✓ pgvector extension enabled")
        
        # Drop existing tables
        print("\n⚠️ Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("✓ Dropped existing tables")
        
        # Create all tables
        print("\n📊 Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created")
        
        # Create indexes
        print("\n⚡ Creating indexes...")
        with engine.connect() as conn:
            # Dense embedding index (HNSW)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS tender_chunks_dense_embedding_idx 
                ON tender_chunks USING hnsw (dense_embedding vector_cosine_ops);
            """))
            
            # Sparse embedding index (GIN)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS tender_chunks_sparse_embedding_idx 
                ON tender_chunks USING gin (sparse_embedding);
            """))
            
            # BM25 tokens index (GIN)
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
        print("✓ All indexes created")
        
        # Verify tables
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
        
        print("\n" + "="*70)
        print("✅ DATABASE SETUP COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ DATABASE SETUP FAILED: {e}")
        raise


# This allows the file to be run directly for testing
# But it's better to use setup_db.py from project root
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    print("⚠️  Running setup.py directly")
    print(f"   Project root: {project_root}")
    print("   Consider using: python setup_db.py from project root\n")
    
    setup_database()