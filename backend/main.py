"""CampusFix AI backend. Run from the backend/ folder:  uvicorn main:app --reload"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import database
from routes import tickets

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="CampusFix AI", lifespan=lifespan)

origins = [o.strip() for o in os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])

app.include_router(tickets.router, prefix="/api")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def ai_configured() -> bool:
    """True if the AI module exists and its environment variables are set. Does not call the model."""
    names = [n.strip() for n in os.getenv("AI_ENV_VARS", "GEMMA_API_KEY").split(",") if n.strip()]
    return tickets.gemma_service is not None and all(os.getenv(n) for n in names)


@app.get("/api/health")
def health():
    try:
        database.ping()
        db = "ok"
    except Exception:
        db = "error"
    return {"status": "ok" if db == "ok" else "degraded", "database": db, "ai_configured": ai_configured()}
