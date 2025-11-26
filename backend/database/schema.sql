-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'uploaded',
    metadata JSONB DEFAULT '{}'::jsonb
);

-- OCR Results table
CREATE TABLE IF NOT EXISTS ocr_results (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    extracted_text TEXT,
    page_number INTEGER,
    confidence_score FLOAT,
    processing_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    config JSONB DEFAULT '{}'::jsonb
);

-- Vector Embeddings table
CREATE TABLE IF NOT EXISTS vector_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(384),  -- Default dimension, adjust as needed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx
ON vector_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Extraction Results table
CREATE TABLE IF NOT EXISTS extraction_results (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    extracted_fields JSONB NOT NULL,
    entities JSONB DEFAULT '{}'::jsonb,
    confidence_score FLOAT,
    processing_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    config JSONB DEFAULT '{}'::jsonb
);

-- Summary Results table
CREATE TABLE IF NOT EXISTS summary_results (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    extractive_summary TEXT,
    abstractive_summary TEXT,
    key_phrases JSONB DEFAULT '[]'::jsonb,
    statistics JSONB DEFAULT '{}'::jsonb,
    processing_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    config JSONB DEFAULT '{}'::jsonb
);

-- Agent Execution Log table
CREATE TABLE IF NOT EXISTS agent_execution_log (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    execution_time FLOAT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    config JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_ocr_results_document_id ON ocr_results(document_id);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_document_id ON vector_embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_extraction_results_document_id ON extraction_results(document_id);
CREATE INDEX IF NOT EXISTS idx_summary_results_document_id ON summary_results(document_id);
CREATE INDEX IF NOT EXISTS idx_agent_log_document_id ON agent_execution_log(document_id);
CREATE INDEX IF NOT EXISTS idx_agent_log_agent_type ON agent_execution_log(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_log_status ON agent_execution_log(status);
