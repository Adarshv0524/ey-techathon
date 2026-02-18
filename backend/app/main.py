import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.api import chat, faq, consent, underwriting, documents
from app.tools.rag.rag_engine import rag_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting TIA-Sales Personal Loan Agent")
    logger.info(f"Tesseract path: {settings.TESSERACT_CMD}")
    logger.info(f"PDF output directory: {settings.OUTPUT_PDF_DIR}")
    
    await rag_engine.initialize()
    logger.info("RAG engine initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TIA-Sales Personal Loan Agent")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(faq.router)
app.include_router(consent.router)
app.include_router(underwriting.router)
app.include_router(documents.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "tesseract_configured": settings.TESSERACT_CMD is not None,
        "pdf_output_dir": settings.OUTPUT_PDF_DIR
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "tesseract_path": settings.TESSERACT_CMD,
        "pdf_generation": "enabled"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
