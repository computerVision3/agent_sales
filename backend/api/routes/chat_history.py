import logging
from psycopg import sql

import json

from settings.db import get_db
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from typing import List, Any

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat History Management"])

class SessionIDsResponse(BaseModel):
    """Response model for unique session IDs."""
    session_ids: List[UUID]


class MessageSessionID(BaseModel):
    message: List[Any]



def _get_session_id(table_name: str) -> sql.Composed:
    """
    Make a SQL query to get session_id.
    """
    return sql.SQL(
        "SELECT DISTINCT session_id FROM {table_name}"
        # "SELECT session_id FROM {table_name}"
    ).format(table_name=sql.Identifier(table_name))

def _messgae_by_session_id(table_name: str) ->sql.Composed:
    """
    get all the message by session id
    """
    return sql.SQL(
        """
        SELECT 
            message->'data'->>'type' AS sender,
            message->'data'->>'content' AS content,
            message->'data'->'tool_calls' AS tool_calls
        FROM {table_name}
        WHERE session_id = %(session_id)s
        ORDER BY id
        """
    ).format(table_name=sql.Identifier(table_name))

def _delete_by_session_id(table_name: str) -> sql.Composed:
    """
    Make a SQL query to delete messages for a given session.
    """
    return sql.SQL(
        "DELETE FROM {table_name} WHERE session_id = %(session_id)s"
    ).format(table_name=sql.Identifier(table_name))

@router.get("/session_id",
            response_model=SessionIDsResponse,
            summary="Get unique sessionIDs",
            description="Fetch all unique `session_id` values from the chat history table.")
async def session_id(db=Depends(get_db)) -> SessionIDsResponse:
    """
    Retrieve all **unique session IDs** stored in the `chat_history` table.
    """
    query = _get_session_id("chat_history")
    logger.info(f"Generated query: {query.as_string(None)}")
    async with get_db() as db:
        await db.execute(query)
        rows = await db.fetchall()
        session_ids = [(row[0]) for row in rows]
        return SessionIDsResponse(session_ids= session_ids)


@router.get("/messages_by_session_id",
            response_model=MessageSessionID,
            summary="Get all Message",
            description="Get `all Message` by sessionID"
            )
async def messages_by_session_id(session_id: UUID, db=Depends(get_db)):
    """
    Get all the messgae by session_id
    """
    query = _messgae_by_session_id("chat_history")
    logger.info(f"Generate: {query.as_string(None)}")
    async with get_db() as db:
        await db.execute(query, {"session_id": session_id})
        rows = await db.fetchall()
        messages = [
            {
                "sender": row[0],
                "content": row[1],
                "tool_calls": row[2] if row[2] is not None else []
            }
            for row in rows
        ]
    return MessageSessionID(message=messages) 
 

@router.delete("/delete_by_session_id",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete chat by sessionID",
               description="""
    `Deletes` all chat history associated with the given `session_id`.

    - Returns **204 No Content** when the deletion is successful (no response body).
    - Returns **404 Not Found** if the session does not exist.
    """,)
async def delete_by_session_id(session_id: UUID, db=Depends(get_db)):
    """
    Delete all query present in session ID
    """
    query = _delete_by_session_id("chat_history")
    logger.info(f"Generate query: {query.as_string(None)}")
    async with get_db() as db:
        result = await db.execute(query, {"session_id": session_id})
        if getattr(result, 'rowcount', 0) == 0:
            raise HTTPException(status_code=404, detail="Session not found")
    return 