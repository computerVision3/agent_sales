from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import chat_history, new_chat, chat, download_file, upload_file

app = FastAPI(title="ReAct AI Agent", version="0.9")

# CORS
origins = [
    "*",
    "http://localhost:3000",
    "http://localhost:5173/",
    "http://192.168.1.152:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization", "Content-Type"],
)


app.mount("/files/output", StaticFiles(directory="/home/ai/Desktop/react-chat-ui/backend/output"), name="output_files")
app.mount("/files/upload", StaticFiles(directory="/home/ai/Desktop/react-chat-ui/backend/upload"), name="upload_files")

# Include routers
app.include_router(new_chat.router)
app.include_router(chat_history.router)
app.include_router(chat.router)
app.include_router(download_file.router)
app.include_router(upload_file.router)

@app.get("/")
async def root():
    return {"message": "Welcome to ReAct agent"}
