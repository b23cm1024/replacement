"""
WorkIQ AI Search Backend — FastAPI Application
================================================
Endpoints:
  GET  /           Health check
  GET  /health      Detailed health check
  POST /upload      Upload a PDF → triggers full ingestion pipeline
  POST /search      Query the ingested documents using RAG

Storage layout (retained permanently on server):
  storage/
    uploads/   ← uploaded PDF files
    images/    ← images extracted from each PDF (sub-folder per document)
"""

import os
import shutil

from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

# ── Database ────────────────────────────────────────────────────────────────────
from app.database import SessionLocal, engine, Base
from app.models import db_models  # noqa: F401 — registers models with Base

# ── Schemas ─────────────────────────────────────────────────────────────────────
from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    UploadResponse,
    GithubIngestRequest,
    GithubIngestResponse,
)

# ── Services ─────────────────────────────────────────────────────────────────────
from app.services.ingestion.document_ingestor import ingest_document
from app.services.ingestion.github_ingestor import ingest_github_repo
from app.services.retrieval.retrieval_service import search_documents
from app.services.retrieval.generation_service import generate_answer


# ── App Setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="WorkIQ AI Search Backend",
    description="Upload PDFs and search them using RAG (LLM-based chunking + vector search).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Persistent storage directories ────────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.getcwd(), "storage", "uploads")
IMAGES_DIR = os.path.join(os.getcwd(), "storage", "images")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


# ── Database table auto-creation on startup ────────────────────────────────────
@app.on_event("startup")
def startup_create_tables():
    """
    Automatically creates DB tables (sources, document_chunks) if they don't
    exist. Safe to call multiple times — SQLAlchemy checks before creating.
    Also ensures the pgvector extension is enabled.
    """
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    print("[Startup] OK - Database tables verified/created.")


# ── Dependency ─────────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "WorkIQ AI Search Backend is running"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "upload_dir": UPLOAD_DIR,
        "images_dir": IMAGES_DIR,
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, Word, Excel, PPT). The server will:
      1. Save it permanently to storage/uploads/
      2. Extract text and images (saved to storage/images/<doc_name>/)
      3. Use Vision AI to describe images
      4. Run LLM-based semantic chunking
      5. Generate embeddings for each chunk
      6. Store everything in PostgreSQL (pgvector)
    """
    ext = file.filename.split('.')[-1].lower()
    allowed_exts = {"pdf", "docx", "pptx", "xlsx", "md"}
    
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Only {', '.join(allowed_exts)} files are supported.")

    file_save_path = os.path.join(UPLOAD_DIR, file.filename)
    doc_name = os.path.splitext(file.filename)[0]
    image_save_dir = os.path.join(IMAGES_DIR, doc_name)

    try:
        # Save uploaded file to server permanently
        with open(file_save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"[Upload] Saved '{file.filename}' to {file_save_path}")

        # Run full universal ingestion pipeline
        result = ingest_document(file_save_path, image_save_dir)

        return UploadResponse(
            status="success",
            filename=file.filename,
            source_id=result["source_id"],
            chunks_stored=result["chunks_stored"],
            message=(
                f"Successfully ingested '{file.filename}'. "
                f"{result['chunks_stored']} semantic chunks are now searchable."
            ),
        )

    except Exception as e:
        # Don't delete the uploaded file — keep it for debugging
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/ingest/github", response_model=GithubIngestResponse)
async def ingest_github(request: GithubIngestRequest):
    """
    Ingest a public GitHub repository into the WorkIQ search index.

    The server will:
      1. Fetch all supported code/text files from the repo via GitHub API
      2. Split each file into semantic chunks using code-structure-aware chunking
         (function/class-level splits per language, sliding window fallback)
      3. Generate vector embeddings for every chunk (BAAI/bge-small-en-v1.5)
      4. Store everything in PostgreSQL (pgvector) — same tables as PDF chunks

    After ingestion, the repo is immediately searchable via POST /search.
    Both PDF and GitHub chunks are searched together in one unified index.
    """
    repo_full = f"{request.owner}/{request.repo}"
    try:
        result = ingest_github_repo(request.owner, request.repo)
        return GithubIngestResponse(
            status="success",
            repo=repo_full,
            source_id=result["source_id"],
            files_processed=result["files_processed"],
            chunks_stored=result["chunks_stored"],
            message=(
                f"Successfully ingested '{repo_full}'. "
                f"{result['files_processed']} files processed, "
                f"{result['chunks_stored']} chunks are now searchable."
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub ingestion failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Query ingested documents using hybrid retrieval (vector + keyword) with
    cross-encoder reranking, followed by LLM answer generation.
    Searches across ALL source types (PDF + GitHub) in one unified index.
    """
    raw_results = search_documents(request.query, db, top_k=request.top_k)

    answer = generate_answer(request.query, raw_results)

    results = [
        SearchResult(
            chunk_text=r["chunk_text"],
            source_name=r.get("source_name"),
            source_type=r.get("source_type"),
            score=r.get("score", 0.0),
        )
        for r in raw_results
    ]

    return SearchResponse(
        query=request.query,
        results=results,
        answer=answer,
    )
