# main.py 
import logging
import sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config.settings import settings
from database.connection import DatabaseConnection 
from routers import ingestion_router, query_router, summary_router

# Configure logging with colored output
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Reduce noise from third-party libraries
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

logger.info("="*70)
logger.info("TENDER MANAGEMENT SYSTEM - STARTING")
logger.info("="*70)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    # Startup
    logger.info("🚀 Application startup initiated")
    logger.debug(f"Configuration: Host={settings.API_HOST}, Port={settings.API_PORT}")
    
    try:
        logger.debug("Initializing database connection pool...")
        DatabaseConnection.initialize_pool()
        logger.info(f"✓ {settings.APP_NAME} v{settings.APP_VERSION} started with SQLAlchemy")
        logger.debug(f"Database: {settings.DB_NAME}@{settings.DB_HOST}:{settings.DB_PORT}")
        logger.debug(f"Embedding Model: {settings.EMBEDDING_MODEL}")
        logger.info("✓ Application startup complete")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutdown initiated")
    try:
        DatabaseConnection.close_all_connections()
        logger.info("✓ Shutdown complete")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}", exc_info=True)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

logger.debug("FastAPI application instance created")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.debug("CORS middleware configured")


# Request/Response Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses"""
    logger.info(f"→ Incoming: {request.method} {request.url.path}")
    logger.debug(f"  Client: {request.client.host if request.client else 'unknown'}")
    logger.debug(f"  Headers: {dict(request.headers)}")
    
    try:
        response = await call_next(request)
        logger.info(f"← Response: {request.method} {request.url.path} - Status {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"✗ Request failed: {request.method} {request.url.path} - {str(e)}", exc_info=True)
        raise


# Routers
logger.debug("Registering API routers...")
app.include_router(ingestion_router.router)
logger.debug("  ✓ Ingestion router registered at /ingest")
app.include_router(query_router.router)
logger.debug("  ✓ Query router registered at /document/{id}/query")
app.include_router(summary_router.router)
logger.debug("  ✓ Summary router registered at /document/{id}/summarize")
logger.info("✓ All API routers registered")


@app.get("/")
def root():
    """Health check"""
    logger.debug("Health check endpoint called")
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "SQLAlchemy"
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    logger.debug("Detailed health check endpoint called")
    
    try:
        # Test database connection
        from database.connection import get_db_session
        from sqlalchemy import text
        
        logger.debug("Testing database connection...")
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        
        logger.debug("Database connection test passed")
        db_status = "connected"
        db_healthy = True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        db_status = f"error: {str(e)}"
        db_healthy = False
    
    health_data = {
        "status": "healthy" if db_healthy else "degraded",
        "components": {
            "api": {"status": "healthy", "version": settings.APP_VERSION},
            "database": {
                "status": db_status,
                "healthy": db_healthy,
                "host": settings.DB_HOST,
                "name": settings.DB_NAME
            }
        }
    }
    
    logger.debug(f"Health check result: {health_data}")
    return health_data


if __name__ == "__main__":
    logger.info("="*70)
    logger.info("Starting uvicorn server...")
    logger.info(f"API URL: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Docs URL: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info(f"Debug mode: ON (reload=True)")
    logger.info("="*70)
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )