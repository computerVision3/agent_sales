from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

async def event_stream():
    for i in range(10):
        await asyncio.sleep(1)  # Simulate response delay
        yield f"data: Message {i}\n\n"

@app.get("/stream")
async def stream_response():
    return StreamingResponse(event_stream(), media_type="text/event-stream")

