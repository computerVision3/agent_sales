import os
import asyncio
from typing import AsyncGenerator, Optional
import psycopg
from psycopg import AsyncConnection
from contextlib import asynccontextmanager
from dotenv import load_dotenv, find_dotenv
from langchain_postgres import PostgresChatMessageHistory

load_dotenv(find_dotenv())

uri: Optional[str] = os.getenv("POSTGRES_URI")
if uri is None:
    raise ValueError("POSTGRES_URI is not set in environment variables")

_pool: Optional[AsyncConnection] = None


async def init_db() -> AsyncConnection:
    """
    Initialize (or reuse) a singleton async DB connection.
    """
    global _pool
    if _pool is None:
        _pool = await psycopg.AsyncConnection.connect(uri)
        # await PostgresChatMessageHistory.acreate_tables( _pool, "chat_history")
  
    return _pool


@asynccontextmanager
async def get_db() -> AsyncGenerator[psycopg.AsyncCursor, None]:
    """
    Provides an async DB cursor with transaction handling.
    Commits on success, rolls back on exception.
    """
    conn = await init_db()
    async with conn.cursor() as cur:
        try:
            yield cur
        except Exception:
            await conn.rollback()
            raise
        else:
            await conn.commit()
