import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException

BASE_TMP_DIR = "tmp/ocr"
MAX_SIZE_MB = 5

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

def save_temp_file(file: UploadFile, session_id: str) -> str:
    ext = os.path.splitext(file.filename.lower())[1]

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = file.file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > MAX_SIZE_MB:
        raise HTTPException(status_code=400, detail="File exceeds 5MB limit")

    doc_id = str(uuid.uuid4())
    session_dir = os.path.join(BASE_TMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    path = os.path.join(session_dir, f"{doc_id}{ext}")
    with open(path, "wb") as f:
        f.write(content)

    return path

def cleanup_session(session_id: str):
    session_dir = os.path.join(BASE_TMP_DIR, session_id)
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
