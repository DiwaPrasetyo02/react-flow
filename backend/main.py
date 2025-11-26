from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes.agent_routes import router as agent_router
from routes.file_routes import router as file_router
from database.db import db
import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    print("🚀 Starting Multi-Agent API Server...")
    print(f"📁 Upload folder: {config.UPLOAD_FOLDER}")

    # Initialize database connection
    try:
        await db.connect()
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("   Server will continue without database functionality")

    # Check API keys
    if config.MISTRAL_API_KEY:
        print("✓ Mistral API key configured")
    else:
        print("⚠ Mistral API key not configured (OCR will use pytesseract only)")

    if config.GEMINI_API_KEY:
        print("✓ Gemini API key configured")
    else:
        print("⚠ Gemini API key not configured (Extraction/Summary will use fallbacks)")

    print("✓ Multi-Agent API Server is ready!")
    print(f"📖 API documentation: http://{config.HOST}:{config.PORT}/docs")

    yield

    # Shutdown
    print("\n🛑 Shutting down Multi-Agent API Server...")
    await db.disconnect()
    print("✓ Shutdown complete")


app = FastAPI(
    title="Multi-Agent Document Processing API",
    description="""
    Production-ready API for document processing with 4-layer agent system:
    - Layer 1: OCR Agent (Mistral Vision + pytesseract)
    - Layer 2: Vector Agent (Sentence Transformers + pgvector)
    - Layer 3: Extraction Agent (Gemini Pro)
    - Layer 4: Summary Agent (Gemini Pro)

    Features:
    - Multi-format document support (PDF, Word, Excel, CSV, Images)
    - Configurable agent parameters
    - Vector similarity search
    - Database persistence with pgvector
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_router, prefix="/api", tags=["agents"])
app.include_router(file_router, prefix="/api/files", tags=["files"])

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "name": "Multi-Agent Document Processing API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "OCR with Mistral Vision",
            "Vector embeddings with pgvector",
            "Entity extraction with Gemini",
            "Document summarization with Gemini",
            "Multi-format document support"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "agents": "/api/agents",
            "files": "/api/files"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    health_status = {
        "status": "healthy",
        "database": "disconnected",
        "apis": {
            "mistral": bool(config.MISTRAL_API_KEY),
            "gemini": bool(config.GEMINI_API_KEY)
        }
    }

    # Check database connection
    if db.pool:
        try:
            await db.fetchval("SELECT 1")
            health_status["database"] = "connected"
        except:
            health_status["database"] = "error"

    return health_status

@app.get("/api/config")
async def get_config():
    """Get system configuration (without sensitive data)"""
    return {
        "upload_folder": str(config.UPLOAD_FOLDER),
        "max_file_size": config.MAX_FILE_SIZE,
        "allowed_extensions": list(config.ALLOWED_EXTENSIONS),
        "ocr_max_pages": config.OCR_MAX_PAGES,
        "vector_dimension": config.VECTOR_DIMENSION,
        "embedding_model": config.EMBEDDING_MODEL,
        "extraction_confidence_threshold": config.EXTRACTION_CONFIDENCE_THRESHOLD,
        "database_enabled": db.pool is not None,
        "apis_configured": {
            "mistral": bool(config.MISTRAL_API_KEY),
            "gemini": bool(config.GEMINI_API_KEY)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level="info"
    )
