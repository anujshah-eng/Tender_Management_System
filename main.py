# main.py 
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config.settings import settings
from database.connection import DatabaseConnection 
from routers import ingestion_router, query_router, summary_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    # Startup
    DatabaseConnection.initialize_pool()
    print(f"✓ {settings.APP_NAME} started with SQLAlchemy")
    
    yield
    
    # Shutdown
    DatabaseConnection.close_all_connections()
    print("✓ Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(ingestion_router.router)
app.include_router(query_router.router)
app.include_router(summary_router.router)


@app.get("/")
def root():
    """Health check"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "SQLAlchemy"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
