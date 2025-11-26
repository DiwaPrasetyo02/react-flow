-- ============================================================================
-- Database Schema with Google Embedding Migration
-- ============================================================================
-- This script creates the complete database schema for Multi-Agent Document Processing
-- and handles migration from old schema (384 dimensions) to new schema (768 dimensions)
--
-- Usage:
--   - Fresh install: Run entire script
--   - Migration: Run entire script (it will handle existing tables safely)
-- ============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- TABLES CREATION
-- ============================================================================

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
-- Default dimension is 768 for Google Embedding API (text-embedding-004)
-- Can be adjusted via VECTOR_DIMENSION config
CREATE TABLE IF NOT EXISTS vector_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(768),  -- Updated for Google Embedding (768 dimensions)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

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

-- ============================================================================
-- MIGRATION: Update vector_embeddings from 384 to 768 dimensions
-- ============================================================================
-- This section handles migration from old schema (sentence-transformers with 384 dims)
-- to new schema (Google Embedding with 768 dims)
-- Safe to run even if already on 768 dimensions

DO $$
DECLARE
    current_dim INTEGER;
    table_exists BOOLEAN;
BEGIN
    -- Check if vector_embeddings table exists
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'vector_embeddings'
    ) INTO table_exists;

    IF table_exists THEN
        -- Check current dimension by querying pg_attribute directly
        SELECT 
            (regexp_match(format_type(a.atttypid, a.atttypmod), 'vector\((\d+)\)'))[1]::INTEGER
        INTO current_dim
        FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = 'public' 
        AND c.relname = 'vector_embeddings' 
        AND a.attname = 'embedding';

        -- Only migrate if dimension is not 768
        IF current_dim IS NOT NULL AND current_dim != 768 THEN
            RAISE NOTICE 'Migrating vector_embeddings from % dimensions to 768 dimensions...', current_dim;
            
            -- Drop existing index
            DROP INDEX IF EXISTS vector_embeddings_embedding_idx;
            
            -- Alter column to 768 dimensions
            -- PostgreSQL will automatically pad with zeros or truncate
            ALTER TABLE vector_embeddings 
            ALTER COLUMN embedding TYPE vector(768);
            
            RAISE NOTICE 'Migration completed successfully.';
        ELSE
            RAISE NOTICE 'vector_embeddings already at 768 dimensions or table is new.';
        END IF;
    ELSE
        RAISE NOTICE 'vector_embeddings table does not exist yet. Will be created with 768 dimensions.';
    END IF;
END $$;

-- ============================================================================
-- INDEXES CREATION
-- ============================================================================

-- Vector similarity search index (recreate if dropped during migration)
CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx
ON vector_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_ocr_results_document_id ON ocr_results(document_id);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_document_id ON vector_embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_extraction_results_document_id ON extraction_results(document_id);
CREATE INDEX IF NOT EXISTS idx_summary_results_document_id ON summary_results(document_id);
CREATE INDEX IF NOT EXISTS idx_agent_log_document_id ON agent_execution_log(document_id);
CREATE INDEX IF NOT EXISTS idx_agent_log_agent_type ON agent_execution_log(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_log_status ON agent_execution_log(status);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify vector_embeddings dimension
DO $$
DECLARE
    dim_result INTEGER;
BEGIN
    SELECT 
        (regexp_match(format_type(a.atttypid, a.atttypmod), 'vector\((\d+)\)'))[1]::INTEGER
    INTO dim_result
    FROM pg_attribute a
    JOIN pg_class c ON a.attrelid = c.oid
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = 'public' 
    AND c.relname = 'vector_embeddings' 
    AND a.attname = 'embedding';
    
    IF dim_result IS NOT NULL THEN
        RAISE NOTICE '✓ vector_embeddings.embedding dimension: %', dim_result;
    ELSE
        RAISE NOTICE '⚠ Could not verify vector_embeddings dimension';
    END IF;
END $$;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. This script is idempotent - safe to run multiple times
-- 2. Migration from 384 to 768 will pad existing vectors with zeros
-- 3. If you need to preserve old embeddings, backup before running migration
-- 4. For fresh installs, tables will be created with 768 dimensions directly
-- 5. Google Embedding API (text-embedding-004) produces 768-dimensional vectors
-- ============================================================================
