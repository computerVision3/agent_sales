from fastapi import APIRouter, UploadFile, HTTPException
import os
import shutil

router = APIRouter(tags=["Upload File"])

# Ensure upload folder exists
UPLOAD_FOLDER = "upload"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile):
    # Check if the uploaded file is a CSV
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    # Full path in the upload folder
    filename = file.filename if file.filename else "uploaded_file.csv"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Save uploaded file to disk
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Return the absolute path
    absolute_path = os.path.abspath(file_path)
    return {"path": absolute_path}
