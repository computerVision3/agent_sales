import logging

import uuid
from fastapi import APIRouter, status
from pydantic import BaseModel

from langchain_postgres import PostgresChatMessageHistory

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Generate SessionID"])

class NewSessionIDsResponse(BaseModel):
    """Response model for unique session IDs."""
    session_id: str

@router.post("/new_chat",
             response_model= NewSessionIDsResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Generate new sessionID",
             description="Generate `new sessionID` to start `new chat`"
             )
async def new_chat():
    session_id = str(uuid.uuid4())
    return NewSessionIDsResponse(session_id=session_id)