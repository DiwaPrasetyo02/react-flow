# Multi-Agent Document Processing Dashboard 🤖

Production-ready dashboard interaktif untuk memproses dokumen menggunakan sistem multi-agent dengan 4 layer. Dibangun dengan React Flow untuk frontend dan FastAPI untuk backend, terintegrasi dengan Mistral AI, Gemini AI, dan pgvector.

## ✨ Fitur Utama

### 🎯 4-Layer Agent System
- **Layer 1: OCR Agent** - Ekstraksi teks dari dokumen dengan Mistral Vision API atau pytesseract
- **Layer 2: Vector & Embedding Agent** - Konversi teks ke vektor embeddings dengan Sentence Transformers + pgvector storage
- **Layer 3: Extraction Agent** - Ekstraksi entitas dan informasi terstruktur dengan Gemini Pro AI
- **Layer 4: Summary Agent** - Pembuatan ringkasan dengan custom prompts menggunakan Gemini Pro AI

### 🎨 Interactive Dashboard
- **Sidebar Navigation** dengan 5 sections: Dashboard, Workflow, Documents, Results, Settings
- **Drag & Drop File Upload** untuk PDF, Word, Excel, CSV, Images
- **Agent Configuration Modal** - Configure setiap agent dengan parameter custom
- **React Flow Canvas** - Visualisasi workflow dengan node connections
- **Real-time Results Panel** - Lihat hasil eksekusi setiap agent
- **Statistics Dashboard** - Track documents processed, success rate, dll

### 🔧 Konfigurasi Per-Agent

#### OCR Agent
- Max pages to process
- Language selection (en, id, es, fr, dll)
- DPI quality (72-600)
- OCR engine (Mistral Vision atau pytesseract)
- Extract images option
- Preserve layout option

#### Vector Agent
- Chunk size (100-2000 characters)
- Chunk overlap (0-500 characters)
- Vector dimension (384/512/768/1024)
- Storage engine (pgvector)
- Index type (IVFFlat atau HNSW)

#### Extraction Agent
- Custom fields extraction (comma-separated)
- Custom field definitions
- Confidence threshold (0-1)
- Enable NER
- Entity types (PERSON, DATE, MONEY, ORG)

#### Summary Agent
- Summary length (short/medium/long)
- Summary type (abstractive/extractive/hybrid)
- Custom prompt untuk goal-oriented summaries
- Temperature control (0-1)
- Include keywords option

## 📁 Struktur Project

```
react-flow/
├── frontend/                          # React application
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.js/css                # Sidebar navigation
│   │   │   ├── FileUpload.js/css             # File upload dengan drag-drop
│   │   │   ├── AgentConfigModal.js/css       # Configuration modal
│   │   │   ├── AgentNode.js/css              # Custom agent nodes
│   │   │   └── ResultsPanel.js/css           # Results display
│   │   ├── pages/
│   │   │   └── Dashboard.js/css              # Main dashboard
│   │   ├── services/
│   │   │   └── api.js                        # API client
│   │   ├── types/
│   │   │   └── agent.js                      # Type definitions
│   │   ├── App.js
│   │   ├── index.js
│   │   └── index.css
│   └── package.json
│
└── backend/                           # FastAPI application
    ├── agents/                        # Agent implementations
    │   ├── base_agent.py             # Base agent class
    │   ├── ocr_agent.py              # OCR with Mistral + pytesseract
    │   ├── vector_agent.py           # Vector embeddings + pgvector
    │   ├── extraction_agent.py       # Extraction with Gemini
    │   └── summary_agent.py          # Summary with Gemini
    ├── database/
    │   ├── db.py                     # Database connection pool
    │   └── schema.sql                # PostgreSQL + pgvector schema
    ├── models/
    │   └── schemas.py                # Pydantic models
    ├── routes/
    │   ├── agent_routes.py           # Agent API endpoints
    │   └── file_routes.py            # File upload endpoints
    ├── utils/
    │   └── document_processor.py     # Document processing utilities
    ├── config.py                     # Configuration management
    ├── main.py                       # FastAPI application
    ├── requirements.txt              # Python dependencies
    └── .env.example                  # Environment variables template
```

## 🚀 Prerequisites

### Software Requirements
- **Node.js** v14+ dan npm
- **Python** 3.8+
- **PostgreSQL** 14+ dengan pgvector extension
- **Tesseract OCR** (optional, untuk OCR fallback)

### API Keys (Required)
- **Mistral API Key** - Untuk OCR dengan vision model (sign up di [mistral.ai](https://mistral.ai))
- **Gemini API Key** - Untuk extraction dan summary (sign up di [ai.google.dev](https://ai.google.dev))

## 📥 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/your-repo/react-flow.git
cd react-flow
```

### 2. Setup Database (PostgreSQL + pgvector)

#### Install PostgreSQL dan pgvector

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install postgresql-14-pgvector

# macOS (with Homebrew)
brew install postgresql
brew install pgvector

# Windows
# Download installer dari https://www.postgresql.org/download/windows/
# Install pgvector dari https://github.com/pgvector/pgvector
```

#### Create Database dan Enable Extension

```bash
# Login ke PostgreSQL
sudo -u postgres psql

# Di dalam psql:
CREATE DATABASE multiagent_db;
\c multiagent_db
CREATE EXTENSION vector;
\q
```

#### Initialize Schema

```bash
cd backend
psql -U postgres -d multiagent_db < database/schema.sql
```

### 3. Setup Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env dan tambahkan API keys
nano .env  # atau gunakan editor favorit Anda
```

#### Edit `.env` file:

```env
# API Keys
MISTRAL_API_KEY=your_mistral_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/multiagent_db
PGVECTOR_ENABLED=true

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True

# File Upload
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=50MB
ALLOWED_EXTENSIONS=pdf,csv,doc,docx,txt,xls,xlsx,jpg,jpeg,png

# Agent Configuration
OCR_MAX_PAGES=50
VECTOR_DIMENSION=384
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EXTRACTION_CONFIDENCE_THRESHOLD=0.7
SUMMARY_MAX_LENGTH=500
```

### 4. Setup Frontend (React)

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template (optional)
cp .env.example .env

# Edit .env jika perlu custom API URL
```

#### Frontend `.env` (optional):

```env
REACT_APP_API_URL=http://localhost:8000/api
```

### 5. Install Tesseract OCR (Optional)

Untuk OCR fallback jika tidak menggunakan Mistral:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-ind

# macOS
brew install tesseract tesseract-lang

# Windows
# Download installer dari https://github.com/UB-Mannheim/tesseract/wiki
```

## 🎮 Menjalankan Aplikasi

### Development Mode

#### Terminal 1: Backend

```bash
cd backend
source venv/bin/activate  # Aktifkan virtual environment
python main.py
```

Backend akan berjalan di: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

#### Terminal 2: Frontend

```bash
cd frontend
npm start
```

Frontend akan berjalan di: **http://localhost:3000**

### Production Mode

#### Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Frontend

```bash
cd frontend
npm run build

# Serve dengan server pilihan Anda (nginx, apache, dll)
# Atau gunakan serve:
npx serve -s build -l 3000
```

## 📖 Cara Penggunaan

### 1. Upload Documents

- Buka **http://localhost:3000**
- Klik menu **Documents** di sidebar
- Drag & drop file atau klik **Browse Files**
- Supported formats: PDF, CSV, Word, Excel, TXT, Images
- File akan langsung di-upload ke server

### 2. Configure Agents

- Klik menu **Workflow** di sidebar
- Klik tombol **⚙️** (gear icon) pada agent node
- Atur parameter sesuai kebutuhan:
  - **OCR**: max pages, language, DPI
  - **Vector**: chunk size, dimension
  - **Extraction**: fields to extract, entity types
  - **Summary**: length, type, custom prompt
- Klik **Save Configuration**

### 3. Execute Agents

- Pada **Workflow** page, klik tombol **Execute** pada agent
- Agent akan memproses dengan konfigurasi yang sudah diatur
- Status akan berubah: idle → running → completed
- Hasil akan muncul otomatis di panel results

### 4. View Results

- Klik menu **Results** di sidebar
- Lihat semua hasil eksekusi agents
- Filter berdasarkan status atau agent type
- Expand result card untuk detail lengkap

### 5. Check Statistics

- Klik menu **Dashboard** di sidebar
- Lihat overview statistics:
  - Total documents processed
  - Success/failure rate
  - Recent activity timeline

## 🔌 API Endpoints

### Agent Endpoints

```http
# Execute agent
POST /api/agents/{agent_type}/execute
Body: {
  "input": "your input data or file path",
  "config": { /* agent configuration */ },
  "parameters": { /* additional parameters */ }
}

# List all agents
GET /api/agents

# Get agent info
GET /api/agents/{agent_type}
```

### File Upload Endpoints

```http
# Upload single file
POST /api/files/upload
FormData: file, description

# Upload multiple files
POST /api/files/upload-multiple
FormData: files[], description

# Process uploaded document
POST /api/files/process/{document_id}

# List documents
GET /api/files/documents?limit=50&offset=0&status=uploaded

# Get document details
GET /api/files/documents/{document_id}

# Delete document
DELETE /api/files/documents/{document_id}
```

### System Endpoints

```http
# Health check
GET /health

# System configuration
GET /api/config

# Root info
GET /
```

## 🧪 Testing

### Test dengan curl

```bash
# Upload file
curl -X POST http://localhost:8000/api/files/upload \
  -F "file=@/path/to/document.pdf" \
  -F "description=Test document"

# Execute OCR agent
curl -X POST http://localhost:8000/api/agents/ocr/execute \
  -H "Content-Type: application/json" \
  -d '{"input": "Sample text for OCR processing"}'

# Health check
curl http://localhost:8000/health
```

### Test dengan Swagger UI

Buka **http://localhost:8000/docs** untuk interactive API documentation.

## 🛠️ Troubleshooting

### Backend tidak bisa start

**Error: Database connection failed**
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Verify connection
psql -U postgres -d multiagent_db -c "SELECT 1;"
```

**Error: ModuleNotFoundError**
```bash
# Pastikan virtual environment aktif
source venv/bin/activate

# Install ulang dependencies
pip install -r requirements.txt
```

**Error: API key not configured**
- Edit file `.env` di folder `backend/`
- Tambahkan MISTRAL_API_KEY dan GEMINI_API_KEY
- Restart backend server

### Frontend tidak bisa connect ke backend

**Error: Network Error atau CORS**
```bash
# Check backend sedang running
curl http://localhost:8000/health

# Check CORS configuration di backend/main.py
# Pastikan frontend URL sudah di allow_origins
```

### pgvector extension not found

```bash
# Install pgvector extension
sudo apt-get install postgresql-14-pgvector

# Enable di database
psql -U postgres -d multiagent_db -c "CREATE EXTENSION vector;"
```

### Upload file failed

```bash
# Check upload folder exists dan writable
ls -la backend/uploads

# Create folder jika belum ada
mkdir -p backend/uploads
chmod 755 backend/uploads
```

## 🔐 Security Notes

⚠️ **IMPORTANT**:
- Jangan commit file `.env` ke repository
- Gunakan `.env.example` sebagai template
- Rotate API keys secara berkala
- Enable HTTPS di production
- Set proper file upload limits
- Validate uploaded files
- Implement rate limiting untuk API

## 📝 Best Practices

### OCR Agent
- Gunakan DPI 300 untuk kualitas optimal
- Batasi max pages untuk dokumen besar (10-20 pages)
- Pilih language yang sesuai dengan dokumen
- Gunakan Mistral untuk handwriting, pytesseract untuk printed text

### Vector Agent
- Chunk size 500-1000 optimal untuk most documents
- Overlap 10-20% dari chunk size
- Vector dimension 384 sudah cukup untuk kebanyakan use cases
- Use IVFFlat untuk speed, HNSW untuk accuracy

### Extraction Agent
- Spesifik field names untuk hasil lebih akurat
- Set confidence threshold 0.7-0.8 untuk balance
- Enable NER untuk automatic entity detection
- Gunakan custom fields untuk domain-specific data

### Summary Agent
- Medium length biasanya paling optimal
- Abstractive untuk creative summaries
- Extractive untuk factual summaries
- Custom prompt sangat membantu untuk specific goals
- Temperature 0.7 untuk balanced creativity/accuracy

## 📚 Documentation

- **Mistral AI**: https://docs.mistral.ai/
- **Google Gemini**: https://ai.google.dev/docs
- **pgvector**: https://github.com/pgvector/pgvector
- **React Flow**: https://reactflow.dev/
- **FastAPI**: https://fastapi.tiangolo.com/

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 👥 Authors

Built with ❤️ using React Flow and FastAPI

---

**Need Help?** Open an issue atau hubungi team support.

**Happy Processing! 🚀**
