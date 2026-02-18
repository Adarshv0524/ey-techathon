# app/main.py

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, faq, underwriting, mock_services, consent


# Load environment variables from backend/.env when present
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")



@asynccontextmanager
async def lifespan(app: FastAPI):
    # No explicit RAG loading here.
    # Domain services (RAG, underwriting) manage themselves.
    yield


app = FastAPI(
    title="TIA-Sales Chat Backend",
    version="0.2.1",
    lifespan=lifespan,
)

# <--- ADD THIS BLOCK --->
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
# <--- END BLOCK --->

# Routers
app.include_router(chat.router)
app.include_router(faq.router)
app.include_router(underwriting.router)
app.include_router(mock_services.router)
app.include_router(consent.router)


@app.get("/health")
def health():
    return {"status": "ok"}
