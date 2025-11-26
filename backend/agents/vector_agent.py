from typing import Any, Dict, List
from .base_agent import BaseAgent
import numpy as np
import config
from database.db import db
import json
import google.generativeai as genai

class VectorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Vector & Embedding Agent", layer=2)
        self.embedding_model = None
        self._initialize_google_embedding()

    def _initialize_google_embedding(self):
        """Initialize Google Embedding API"""
        try:
            if not config.GEMINI_API_KEY:
                print("⚠ Gemini API key not configured. Vector Agent will not work.")
                return
            
            genai.configure(api_key=config.GEMINI_API_KEY)
            # Use text-embedding-004 (768 dimensions) or embedding-001 (768 dimensions)
            # Default to text-embedding-004 for better quality
            # Check if config model is a Google embedding model, otherwise use default
            if config.EMBEDDING_MODEL and (
                config.EMBEDDING_MODEL.startswith('text-embedding') or 
                config.EMBEDDING_MODEL.startswith('embedding-')
            ):
                self.embedding_model = config.EMBEDDING_MODEL
            else:
                self.embedding_model = 'text-embedding-004'
            print(f"✓ Initialized Google Embedding API with model: {self.embedding_model}")
        except Exception as e:
            print(f"⚠ Failed to initialize Google Embedding: {e}")
            print("  Please check GEMINI_API_KEY configuration")

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using Google Embedding API
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self.embedding_model:
            raise Exception("Google Embedding API not initialized. Please check GEMINI_API_KEY.")
        
        try:
            # Google Embedding API call
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"  # or "retrieval_query" for queries
            )
            
            # Extract embedding from result
            embedding = result['embedding']
            return embedding
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")

    async def execute(self, input_data: Any, parameters: Dict = None) -> Dict[str, Any]:
        """
        Generate vector embeddings using Google Embedding API and store in pgvector database

        Args:
            input_data: Text content or OCR result to vectorize
            parameters: Configuration including chunk_size, overlap, dimension, etc.

        Returns:
            Dictionary containing embedding information and storage results
        """
        if not self.embedding_model:
            raise Exception("Google Embedding API not initialized. Please configure GEMINI_API_KEY.")

        params = parameters or {}
        chunk_size = params.get('chunkSize', 500)
        chunk_overlap = params.get('chunkOverlap', 50)
        vector_dim = params.get('vectorDimension', config.VECTOR_DIMENSION)
        storage_engine = params.get('storageEngine', 'pgvector')
        index_type = params.get('indexType', 'ivfflat')
        document_id = params.get('document_id', None)

        try:
            # Extract text from input
            text = await self._extract_text(input_data)

            if not text or len(text.strip()) == 0:
                raise Exception("No text content to vectorize")

            # Split text into chunks
            chunks = self._chunk_text(text, chunk_size, chunk_overlap)

            # Generate embeddings for each chunk using Google Embedding API
            embeddings_data = []
            for chunk in chunks:
                # Generate embedding via Google API
                embedding = await self._generate_embedding(chunk['text'])
                embedding = np.array(embedding)

                # Google embedding models produce 768 dimensions by default
                # Resize to match configured dimension if needed
                if len(embedding) != vector_dim:
                    if len(embedding) > vector_dim:
                        # Truncate if larger
                        embedding = embedding[:vector_dim]
                    else:
                        # Pad with zeros if smaller
                        embedding = np.pad(
                            embedding,
                            (0, vector_dim - len(embedding)),
                            mode='constant'
                        )

                embeddings_data.append({
                    "chunk_index": chunk['chunk_index'],
                    "text": chunk['text'],
                    "embedding": embedding.tolist(),
                    "vector_norm": float(np.linalg.norm(embedding)),
                    "start_pos": chunk['start_pos'],
                    "end_pos": chunk['end_pos'],
                    "length": chunk['length']
                })

            # Store embeddings in database if document_id is provided
            stored_count = 0
            if document_id and storage_engine == 'pgvector':
                stored_count = await self._store_embeddings(
                    document_id, embeddings_data, index_type
                )

            # Calculate statistics
            all_norms = [e['vector_norm'] for e in embeddings_data]
            avg_norm = float(np.mean(all_norms))

            return {
                "total_chunks": len(chunks),
                "embeddings_generated": len(embeddings_data),
                "embeddings_stored": stored_count,
                "embedding_dimension": vector_dim,
                "embedding_model": self.embedding_model,
                "embedding_provider": "google",
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "average_vector_norm": round(avg_norm, 4),
                "storage_engine": storage_engine,
                "index_type": index_type,
                "chunks_preview": [
                    {
                        "chunk_id": e['chunk_index'],
                        "text_preview": e['text'][:100] + "..." if len(e['text']) > 100 else e['text'],
                        "vector_norm": e['vector_norm'],
                        "embedding_preview": e['embedding'][:5]  # First 5 dimensions
                    }
                    for e in embeddings_data[:3]  # First 3 chunks
                ],
                "similarity_search_ready": stored_count > 0
            }

        except Exception as e:
            raise Exception(f"Vector embedding failed: {str(e)}")

    async def _extract_text(self, input_data: Any) -> str:
        """Extract text from various input formats"""
        if isinstance(input_data, str):
            return input_data
        elif isinstance(input_data, dict):
            # Try to extract from OCR result
            if 'extracted_text' in input_data:
                return input_data['extracted_text']
            elif 'full_text' in input_data:
                return input_data['full_text']
            elif 'output' in input_data and isinstance(input_data['output'], dict):
                if 'extracted_text' in input_data['output']:
                    return input_data['output']['extracted_text']
            # Try to serialize as JSON
            return json.dumps(input_data)
        else:
            return str(input_data)

    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to split
            chunk_size: Maximum size of each chunk (in characters)
            overlap: Number of characters to overlap between chunks

        Returns:
            List of dictionaries containing chunks and metadata
        """
        chunks = []
        start = 0
        text_length = len(text)
        chunk_index = 0

        while start < text_length:
            end = min(start + chunk_size, text_length)

            # Try to break at sentence boundary if possible
            if end < text_length:
                # Look for sentence endings near the chunk boundary
                for boundary_char in ['. ', '.\n', '! ', '? ']:
                    boundary_pos = text.rfind(boundary_char, start, end)
                    if boundary_pos > start + chunk_size // 2:  # Found a good break point
                        end = boundary_pos + len(boundary_char)
                        break

            chunk_text = text[start:end].strip()

            if chunk_text:  # Only add non-empty chunks
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "start_pos": start,
                    "end_pos": end,
                    "length": len(chunk_text)
                })
                chunk_index += 1

            # Move to next chunk with overlap
            start = end - overlap if end < text_length else text_length

        return chunks

    async def _store_embeddings(
        self,
        document_id: int,
        embeddings_data: List[Dict[str, Any]],
        index_type: str
    ) -> int:
        """
        Store embeddings in pgvector database

        Args:
            document_id: ID of the document
            embeddings_data: List of embeddings with metadata
            index_type: Type of index to use (ivfflat or hnsw)

        Returns:
            Number of embeddings stored
        """
        if not db.pool:
            print("⚠ Database not connected, skipping storage")
            return 0

        try:
            stored_count = 0
            async with db.get_connection() as conn:
                for emb_data in embeddings_data:
                    # Convert embedding list to pgvector format
                    embedding_str = '[' + ','.join(map(str, emb_data['embedding'])) + ']'

                    # Insert into database
                    await conn.execute("""
                        INSERT INTO vector_embeddings
                        (document_id, chunk_text, chunk_index, embedding, metadata)
                        VALUES ($1, $2, $3, $4::vector, $5)
                    """,
                        document_id,
                        emb_data['text'],
                        emb_data['chunk_index'],
                        embedding_str,
                        json.dumps({
                            'vector_norm': emb_data['vector_norm'],
                            'start_pos': emb_data['start_pos'],
                            'end_pos': emb_data['end_pos'],
                            'length': emb_data['length']
                        })
                    )
                    stored_count += 1

            print(f"✓ Stored {stored_count} embeddings for document {document_id}")
            return stored_count

        except Exception as e:
            print(f"⚠ Failed to store embeddings: {e}")
            return 0

    async def similarity_search(
        self,
        query_text: str,
        document_id: int = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search on stored embeddings using Google Embedding API

        Args:
            query_text: Query text to search for
            document_id: Optional document ID to limit search
            top_k: Number of results to return

        Returns:
            List of similar chunks with scores
        """
        if not self.embedding_model:
            raise Exception("Google Embedding API not initialized")

        if not db.pool:
            raise Exception("Database not connected")

        try:
            # Generate query embedding using Google API
            # Use retrieval_query task type for queries
            result = genai.embed_content(
                model=self.embedding_model,
                content=query_text,
                task_type="retrieval_query"
            )
            query_embedding = np.array(result['embedding'])
            
            # Resize to match stored embedding dimension if needed
            vector_dim = config.VECTOR_DIMENSION
            if len(query_embedding) != vector_dim:
                if len(query_embedding) > vector_dim:
                    query_embedding = query_embedding[:vector_dim]
                else:
                    query_embedding = np.pad(
                        query_embedding,
                        (0, vector_dim - len(query_embedding)),
                        mode='constant'
                    )
            
            embedding_str = '[' + ','.join(map(str, query_embedding.tolist())) + ']'

            # Build query
            if document_id:
                query = """
                    SELECT chunk_text, chunk_index, metadata,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM vector_embeddings
                    WHERE document_id = $2
                    ORDER BY embedding <=> $1::vector
                    LIMIT $3
                """
                params = [embedding_str, document_id, top_k]
            else:
                query = """
                    SELECT chunk_text, chunk_index, document_id, metadata,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM vector_embeddings
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                """
                params = [embedding_str, top_k]

            results = await db.fetch(query, *params)

            return [
                {
                    "chunk_text": row['chunk_text'],
                    "chunk_index": row['chunk_index'],
                    "document_id": row.get('document_id'),
                    "similarity": float(row['similarity']),
                    "metadata": json.loads(row['metadata']) if row['metadata'] else {}
                }
                for row in results
            ]

        except Exception as e:
            raise Exception(f"Similarity search failed: {str(e)}")
