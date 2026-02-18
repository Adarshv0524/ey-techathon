import logging
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from app.core.session import session_manager
from app.config import settings
from app.tools.document_ocr.ocr_engine import ocr_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

SUPPORTED_DOC_TYPES = {"salary_slip", "pan_card", "aadhaar"}


@router.post("/upload")
async def upload_document(session_id: str, doc_type: str, file: UploadFile = File(...)):
    """
    Upload a document and run OCR extraction.
    """
    if doc_type not in SUPPORTED_DOC_TYPES:
        raise HTTPException(status_code=400, detail="Invalid doc_type")

    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.SUPPORTED_IMAGE_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_bytes = await file.read()
    max_size_bytes = int(settings.MAX_FILE_SIZE_MB * 1024 * 1024)
    if len(file_bytes) > max_size_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    if ext == ".pdf":
        result = await ocr_engine.process_pdf(file_bytes, doc_type)
    else:
        result = await ocr_engine.process_image(file_bytes, doc_type)

    status = result.get("status", "ERROR")
    confidence = result.get("confidence", 0.0)
    extracted = result.get("extracted_data", {})

    documents = session.get_slot("documents") or {}
    documents[doc_type] = {
        "filename": file.filename,
        "status": status,
        "confidence": confidence,
        "uploaded_at": datetime.utcnow().isoformat()
    }
    session.update_slot("documents", documents)

    if extracted:
        ocr_data = session.get_slot("ocr_data") or {}
        ocr_data[doc_type] = extracted
        session.update_slot("ocr_data", ocr_data)

    await session_manager.update_session(session)

    # If user is already in document upload stage, keep state as-is.
    # Otherwise, allow the flow to reach document upload naturally via chat.

    if status == "LOW_CONFIDENCE":
        message = "Document unclear. Please re-upload a sharper image."
    elif status == "NO_TEXT_DETECTED":
        message = "No text detected. If this is a scanned PDF, try uploading a clear image."
    elif status == "SUCCESS":
        message = "Document processed."
    else:
        message = result.get("error") or "Document processing failed."

    return {
        "status": status,
        "confidence": confidence,
        "extracted_data": extracted,
        "message": message
    }


@router.get("/download/{session_id}")
async def download_decision_document(session_id: str):
    """
    Download the generated loan decision PDF document
    """
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        pdf_path = session.get_slot("decision_document")
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="Decision document not found")
        
        filename = os.path.basename(pdf_path)
        
        return FileResponse(
            path=pdf_path,
            media_type='application/pdf',
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to download document")


@router.get("/list/{session_id}")
async def list_session_documents(session_id: str):
    """
    List all generated documents for a session
    """
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        pdf_path = session.get_slot("decision_document")
        
        documents = []
        if pdf_path and os.path.exists(pdf_path):
            stat_info = os.stat(pdf_path)
            documents.append({
                "filename": os.path.basename(pdf_path),
                "path": pdf_path,
                "size_bytes": stat_info.st_size,
                "created_at": stat_info.st_ctime,
                "download_url": f"/api/documents/download/{session_id}"
            })
        
        return {
            "session_id": session_id,
            "documents": documents
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")
