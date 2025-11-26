from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from pathlib import Path
import aiofiles
import uuid
from datetime import datetime
import config
from database.db import db
from utils.document_processor import DocumentProcessor

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """
    Upload a document file

    Supports: PDF, CSV, Word, Excel, TXT, Images
    """
    # Validate file type
    file_ext = Path(file.filename).suffix.lower().lstrip('.')

    if file_ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not allowed. Supported: {', '.join(config.ALLOWED_EXTENSIONS)}"
        )

    try:
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        safe_filename = f"{unique_id}_{file.filename}"
        file_path = config.UPLOAD_FOLDER / safe_filename

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        file_size = len(content)

        # Store in database
        if db.pool:
            document_id = await db.fetchval("""
                INSERT INTO documents
                (filename, file_type, file_size, status, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """,
                file.filename,
                file_ext,
                file_size,
                'uploaded',
                '{"description": "' + (description or '') + '"}'
            )
        else:
            document_id = unique_id

        return {
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "file_size": file_size,
            "file_type": file_ext,
            "file_path": str(file_path),
            "message": "File uploaded successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload-multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    description: Optional[str] = Form(None)
):
    """Upload multiple documents at once"""
    results = []
    errors = []

    for file in files:
        try:
            result = await upload_file(file, description)
            results.append(result)
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })

    return {
        "success": len(errors) == 0,
        "uploaded": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


@router.post("/process/{document_id}")
async def process_document(document_id: int):
    """
    Process an uploaded document (extract content)

    This endpoint extracts text and metadata from the uploaded file
    """
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Get document info
        doc = await db.fetchrow("""
            SELECT id, filename, file_type, file_size
            FROM documents
            WHERE id = $1
        """, document_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Find file path
        file_pattern = f"*_{doc['filename']}"
        matching_files = list(config.UPLOAD_FOLDER.glob(file_pattern))

        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found on disk")

        file_path = matching_files[0]

        # Process document
        processor = DocumentProcessor()
        result = await processor.process_file(file_path, doc['file_type'])

        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])

        # Update document status
        await db.execute("""
            UPDATE documents
            SET status = $1, metadata = metadata || $2
            WHERE id = $3
        """,
            'processed',
            '{"processed_at": "' + datetime.now().isoformat() + '"}',
            document_id
        )

        return {
            "success": True,
            "document_id": document_id,
            "processing_result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/documents")
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
):
    """List all uploaded documents"""
    if not db.pool:
        return {
            "documents": [],
            "total": 0,
            "message": "Database not available"
        }

    try:
        # Build query
        if status:
            query = """
                SELECT id, filename, file_type, file_size, upload_date, status
                FROM documents
                WHERE status = $1
                ORDER BY upload_date DESC
                LIMIT $2 OFFSET $3
            """
            docs = await db.fetch(query, status, limit, offset)
            count = await db.fetchval(
                "SELECT COUNT(*) FROM documents WHERE status = $1",
                status
            )
        else:
            query = """
                SELECT id, filename, file_type, file_size, upload_date, status
                FROM documents
                ORDER BY upload_date DESC
                LIMIT $1 OFFSET $2
            """
            docs = await db.fetch(query, limit, offset)
            count = await db.fetchval("SELECT COUNT(*) FROM documents")

        return {
            "documents": [
                {
                    "id": doc['id'],
                    "filename": doc['filename'],
                    "file_type": doc['file_type'],
                    "file_size": doc['file_size'],
                    "upload_date": doc['upload_date'].isoformat(),
                    "status": doc['status']
                }
                for doc in docs
            ],
            "total": count,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/documents/{document_id}")
async def get_document(document_id: int):
    """Get document details"""
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        doc = await db.fetchrow("""
            SELECT d.*,
                   (SELECT COUNT(*) FROM ocr_results WHERE document_id = d.id) as ocr_count,
                   (SELECT COUNT(*) FROM vector_embeddings WHERE document_id = d.id) as embedding_count,
                   (SELECT COUNT(*) FROM extraction_results WHERE document_id = d.id) as extraction_count,
                   (SELECT COUNT(*) FROM summary_results WHERE document_id = d.id) as summary_count
            FROM documents d
            WHERE d.id = $1
        """, document_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "id": doc['id'],
            "filename": doc['filename'],
            "file_type": doc['file_type'],
            "file_size": doc['file_size'],
            "upload_date": doc['upload_date'].isoformat(),
            "status": doc['status'],
            "metadata": doc['metadata'],
            "processing_counts": {
                "ocr": doc['ocr_count'],
                "embeddings": doc['embedding_count'],
                "extractions": doc['extraction_count'],
                "summaries": doc['summary_count']
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """Delete a document and its associated data"""
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Get document info
        doc = await db.fetchrow("""
            SELECT filename FROM documents WHERE id = $1
        """, document_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from database (cascade will remove related data)
        await db.execute("DELETE FROM documents WHERE id = $1", document_id)

        # Delete file from disk
        file_pattern = f"*_{doc['filename']}"
        matching_files = list(config.UPLOAD_FOLDER.glob(file_pattern))
        for file_path in matching_files:
            try:
                file_path.unlink()
            except:
                pass

        return {
            "success": True,
            "message": f"Document {document_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
