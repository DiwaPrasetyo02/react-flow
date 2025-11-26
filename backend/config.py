import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# API Keys
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/multiagent_db"
)
PGVECTOR_ENABLED = os.getenv("PGVECTOR_ENABLED", "true").lower() == "true"

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# File Upload Configuration
UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", "./uploads"))
UPLOAD_FOLDER.mkdir(exist_ok=True)
MAX_FILE_SIZE = os.getenv("MAX_FILE_SIZE", "50MB")
ALLOWED_EXTENSIONS = set(
    os.getenv("ALLOWED_EXTENSIONS", "pdf,csv,doc,docx,txt,xls,xlsx").split(",")
)

# Agent Configuration
OCR_MAX_PAGES = int(os.getenv("OCR_MAX_PAGES", 50))
# Google Embedding models produce 768 dimensions by default
# Can be resized to match VECTOR_DIMENSION if needed
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", 768))
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "text-embedding-004"  # Google Embedding model (768 dimensions)
)
EXTRACTION_CONFIDENCE_THRESHOLD = float(
    os.getenv("EXTRACTION_CONFIDENCE_THRESHOLD", 0.7)
)
SUMMARY_MAX_LENGTH = int(os.getenv("SUMMARY_MAX_LENGTH", 500))
