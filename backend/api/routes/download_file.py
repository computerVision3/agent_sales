from fastapi.responses import FileResponse
import os
from fastapi import APIRouter

router = APIRouter(tags=["Download File"])

@router.get("/download")
def download_file(path: str):
    if os.path.exists(path):
        filename = os.path.basename(path) 
        return FileResponse(path, filename=filename)
    else:
        return {"error": "File not found"}
