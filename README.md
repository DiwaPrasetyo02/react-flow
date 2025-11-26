# Multi-Agent Dashboard with React Flow

Sebuah dashboard interaktif yang menampilkan sistem multi-agent dengan 4 layer menggunakan React Flow untuk frontend dan FastAPI untuk backend.

## Fitur

- **4 Layer Agent System:**
  - Layer 1: OCR Agent - Ekstraksi teks dari gambar
  - Layer 2: Vector & Embedding Agent - Konversi teks ke vektor embedding
  - Layer 3: Extraction Agent - Ekstraksi entitas dan informasi terstruktur
  - Layer 4: Summary Agent - Pembuatan ringkasan teks

- **Interactive Dashboard:**
  - Visualisasi workflow dengan React Flow
  - Eksekusi agent secara individual
  - Panel hasil real-time
  - Status tracking untuk setiap agent

## Struktur Project

```
react-flow/
├── frontend/                 # React application
│   ├── public/
│   ├── src/
│   │   ├── components/      # Komponen React
│   │   │   ├── AgentNode.js
│   │   │   ├── AgentNode.css
│   │   │   ├── ResultsPanel.js
│   │   │   └── ResultsPanel.css
│   │   ├── pages/           # Pages
│   │   │   ├── Dashboard.js
│   │   │   └── Dashboard.css
│   │   ├── services/        # API services
│   │   │   └── api.js
│   │   ├── types/           # Type definitions
│   │   │   └── agent.js
│   │   ├── App.js
│   │   ├── index.js
│   │   └── index.css
│   └── package.json
│
└── backend/                  # FastAPI application
    ├── agents/              # Agent implementations
    │   ├── base_agent.py
    │   ├── ocr_agent.py
    │   ├── vector_agent.py
    │   ├── extraction_agent.py
    │   └── summary_agent.py
    ├── models/              # Pydantic models
    │   └── schemas.py
    ├── routes/              # API routes
    │   └── agent_routes.py
    ├── main.py             # FastAPI app
    └── requirements.txt
```

## Prerequisites

- Node.js (v14 atau lebih tinggi)
- Python 3.8+
- npm atau yarn

## Instalasi

### 1. Setup Backend (FastAPI)

```bash
# Masuk ke direktori backend
cd backend

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Untuk Linux/Mac:
source venv/bin/activate
# Untuk Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Frontend (React)

```bash
# Masuk ke direktori frontend
cd frontend

# Install dependencies
npm install
```

## Menjalankan Aplikasi

### 1. Jalankan Backend

```bash
cd backend
source venv/bin/activate  # Aktifkan virtual environment
python main.py
```

Backend akan berjalan di: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 2. Jalankan Frontend

Di terminal baru:

```bash
cd frontend
npm start
```

Frontend akan berjalan di: `http://localhost:3000`

## Penggunaan

1. Buka browser dan akses `http://localhost:3000`
2. Anda akan melihat dashboard dengan 4 agent nodes yang tersusun secara vertikal
3. Masukkan input data di text area di bagian atas
4. Klik tombol "Execute" pada agent yang ingin dijalankan
5. Hasil eksekusi akan muncul di panel "Agent Results" di bagian bawah

### Contoh Input

```
Sample input for OCR agent. This text will be processed by the OCR system to extract meaningful information. Email: test@example.com, Date: 01/01/2024
```

## API Endpoints

### Execute Agent
```
POST /api/agents/{agent_type}/execute
```

Body:
```json
{
  "input": "your input data",
  "parameters": {}
}
```

Agent types: `ocr`, `vector`, `extraction`, `summary`

### List All Agents
```
GET /api/agents
```

### Get Agent Info
```
GET /api/agents/{agent_type}
```

### Health Check
```
GET /health
```

## Detail Agent

### Layer 1: OCR Agent
- Mengekstraksi teks dari input
- Memberikan confidence score untuk setiap kata
- Output: extracted text, word confidences, statistics

### Layer 2: Vector & Embedding Agent
- Mengkonversi teks menjadi vector embeddings
- Membagi teks menjadi chunks
- Output: embeddings, chunks, vector norms

### Layer 3: Extraction Agent
- Mengekstrak entitas (dates, emails, numbers, keywords)
- Membuat structured data
- Output: entities, structured data, confidence score

### Layer 4: Summary Agent
- Membuat ringkasan extractive dan abstractive
- Menghitung statistik teks
- Output: summaries, statistics, key phrases

## Teknologi yang Digunakan

### Frontend
- React 18
- React Flow 11
- Axios
- CSS3

### Backend
- FastAPI
- Pydantic
- Uvicorn
- NumPy
- PIL (Pillow)

## Development

### Menambah Agent Baru

1. Buat file agent baru di `backend/agents/`
2. Extend dari `BaseAgent` class
3. Implement method `execute()`
4. Register agent di `routes/agent_routes.py`
5. Tambahkan node di frontend `pages/Dashboard.js`

### Contoh Agent Baru

```python
from .base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__("My New Agent", layer=5)

    async def execute(self, input_data, parameters=None):
        # Your logic here
        return {"result": "processed data"}
```

## Testing API

Menggunakan curl:

```bash
# Execute OCR Agent
curl -X POST "http://localhost:8000/api/agents/ocr/execute" \
  -H "Content-Type: application/json" \
  -d '{"input": "Sample text for OCR"}'

# List all agents
curl "http://localhost:8000/api/agents"
```

Atau buka Swagger UI di: `http://localhost:8000/docs`

## Troubleshooting

### Backend tidak bisa dijalankan
- Pastikan virtual environment sudah diaktifkan
- Install ulang dependencies: `pip install -r requirements.txt`

### Frontend tidak bisa connect ke backend
- Pastikan backend berjalan di port 8000
- Check CORS settings di `backend/main.py`

### Node tidak muncul di React Flow
- Clear browser cache
- Restart development server

## License

MIT

## Author

Dibuat dengan React Flow dan FastAPI
