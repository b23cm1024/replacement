"""
Zephyr AI Search Backend — FastAPI Application
================================================
Endpoints:
  GET    /               Health check
  GET    /health         Detailed health check
  POST   /upload         Upload a document (PDF, DOCX, PPTX, XLSX)
  POST   /ingest/github  Ingest a GitHub repository
  POST   /ingest/s3      Ingest all documents from an S3 bucket prefix
  POST   /search         Query the ingested documents using RAG
  GET    /sources        List all ingested sources
  DELETE /sources/{id}   Delete a source and all its chunks
"""

import os
import shutil

from fastapi import FastAPI, Depends, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from dotenv import load_dotenv

load_dotenv()

# ── Database ────────────────────────────────────────────────────────────────────
from app.database import SessionLocal, engine, Base
from app.models import db_models  # noqa: F401 — registers models with Base
from app.models.db_models import Source, DocumentChunk

# ── Schemas ─────────────────────────────────────────────────────────────────────
from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    UploadResponse,
    GithubIngestRequest,
    GithubIngestResponse,
    S3IngestRequest,
    S3IngestResponse,
    S3FileResult,
    SourceSchema,
    SourcesListResponse,
    DeleteResponse,
)

# ── Services ─────────────────────────────────────────────────────────────────────
from app.services.ingestion.document_ingestor import ingest_document
from app.services.ingestion.github_ingestor import ingest_github_repo
from app.services.ingestion.s3_ingestor import ingest_from_s3
from app.services.retrieval.retrieval_service import search_documents
from app.services.retrieval.generation_service import generate_answer


# ── App Setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Zephyr AI Search Backend",
    description="Upload documents and GitHub repos, then search them using RAG (semantic chunking + vector search + LLM).",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when allow_origins=["*"] to satisfy browser CORS spec
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
    return {"status": "ok", "message": "Zephyr AI Search Backend is running"}


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
      3. Use Vision AI to describe images (if OpenAI key is funded)
      4. Run LLM-based semantic chunking (falls back to paragraph chunking)
      5. Generate embeddings for each chunk
      6. Store everything in PostgreSQL (pgvector)
    """
    # Sanitize filename to prevent directory traversal attacks (e.g. "../../etc/passwd")
    safe_filename = os.path.basename(file.filename or "").strip()
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    ext = safe_filename.split('.')[-1].lower()
    allowed_exts = {"pdf", "docx", "pptx", "xlsx", "md"}

    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(allowed_exts))}"
        )

    file_save_path = os.path.join(UPLOAD_DIR, safe_filename)
    doc_name = os.path.splitext(safe_filename)[0]
    image_save_dir = os.path.join(IMAGES_DIR, doc_name)

    try:
        with open(file_save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"[Upload] Saved '{safe_filename}' to {file_save_path}")

        result = ingest_document(file_save_path, image_save_dir)

        return UploadResponse(
            status="success",
            filename=safe_filename,
            source_id=result["source_id"],
            chunks_stored=result["chunks_stored"],
            message=(
                f"Successfully ingested '{safe_filename}'. "
                f"{result['chunks_stored']} semantic chunks are now searchable."
            ),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/ingest/github", response_model=GithubIngestResponse)
async def ingest_github(request: GithubIngestRequest):
    """
    Ingest a public (or private, if token is provided) GitHub repository.

    The server will:
      1. Fetch all supported code/text files from the repo via GitHub API
      2. Split each file into semantic chunks using language-aware chunking
      3. Generate vector embeddings for every chunk
      4. Store everything in PostgreSQL (pgvector)
    """
    repo_full = f"{request.owner}/{request.repo}"
    try:
        # Pass optional per-request token; falls back to GITHUB_TOKEN env var inside the client
        result = ingest_github_repo(request.owner, request.repo, token=request.token)
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


@app.post("/ingest/s3", response_model=S3IngestResponse)
async def ingest_s3(request: S3IngestRequest):
    """
    Ingest all supported documents from an S3 bucket prefix.

    The server will:
      1. List all PDF, DOCX, PPTX, XLSX, MD files under the given prefix
      2. Download each file to a temporary directory
      3. Run through the full ingestion pipeline:
         - Parse text + images (Docling)
         - Vision AI image descriptions (OpenAI)
         - LLM semantic chunking
         - Generate vector embeddings
         - Store in PostgreSQL (pgvector)
      4. Clean up temp files

    Defaults to bucket='zephyr-wings' and prefix='raw_data/' if not specified.
    """
    try:
        result = ingest_from_s3(request.bucket, request.prefix)

        status = "success" if result["files_skipped"] == 0 else "partial"
        message = (
            f"Scanned s3://{request.bucket}/{request.prefix} — "
            f"{result['files_found']} file(s) found, "
            f"{result['files_ingested']} ingested, "
            f"{result['files_skipped']} skipped, "
            f"{result['total_chunks']} total chunks stored."
        )

        return S3IngestResponse(
            status=status,
            bucket=request.bucket,
            prefix=request.prefix,
            files_found=result["files_found"],
            files_ingested=result["files_ingested"],
            files_skipped=result["files_skipped"],
            total_chunks=result["total_chunks"],
            message=message,
            results=[
                S3FileResult(
                    s3_key=r["s3_key"],
                    filename=r["filename"],
                    status=r["status"],
                    source_id=r.get("source_id"),
                    chunks_stored=r.get("chunks_stored"),
                    error=r.get("error"),
                )
                for r in result["results"]
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 ingestion failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Query ingested documents using hybrid retrieval (vector + keyword) with
    cross-encoder reranking, followed by LLM answer generation.
    Searches across ALL source types in one unified index.
    """
    raw_results = search_documents(
        request.query,
        db,
        top_k=request.top_k,
        source_type=request.source_type,  # Honour optional source filter from UI
    )

    answer = generate_answer(request.query, raw_results)

    results = [
        SearchResult(
            chunk_text=r["chunk_text"],
            source_name=r.get("source_name"),
            source_type=r.get("source_type"),
            score=r.get("score", 0.0),
            metadata=r.get("metadata") or {},
        )
        for r in raw_results
    ]

    return SearchResponse(
        query=request.query,
        results=results,
        answer=answer,
    )


@app.get("/sources", response_model=SourcesListResponse)
def list_sources(
    source_type: str = None,
    db: Session = Depends(get_db),
):
    """
    Return all ingested sources with their chunk counts.
    Optionally filter by source_type (pdf, github, docx, pptx, xlsx).
    """
    # Subquery: count chunks per source
    chunk_counts = (
        db.query(
            DocumentChunk.source_id,
            func.count(DocumentChunk.id).label("chunk_count"),
        )
        .group_by(DocumentChunk.source_id)
        .subquery()
    )

    query = db.query(Source, chunk_counts.c.chunk_count).outerjoin(
        chunk_counts, Source.id == chunk_counts.c.source_id
    )

    if source_type:
        query = query.filter(Source.source_type == source_type)

    rows = query.order_by(Source.id.desc()).all()

    sources = [
        SourceSchema(
            id=source.id,
            source_type=source.source_type,
            source_name=source.source_name,
            source_identifier=source.source_identifier,
            ingested_at=None,    # Column not yet in DB; can be added later
            chunk_count=count or 0,
        )
        for source, count in rows
    ]

    return SourcesListResponse(sources=sources, total=len(sources))


@app.delete("/sources/{source_id}", response_model=DeleteResponse)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """
    Delete a source and ALL its associated chunks from the database.
    This is irreversible.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found.")

    name = source.source_name
    # Delete chunks first (FK constraint)
    db.query(DocumentChunk).filter(DocumentChunk.source_id == source_id).delete()
    db.delete(source)
    db.commit()

    return DeleteResponse(
        status="success",
        message=f"Source '{name}' (ID {source_id}) and all its chunks have been deleted.",
    )
