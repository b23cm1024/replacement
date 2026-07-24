from pydantic import BaseModel
from typing import Any, Dict, List, Optional


# ── Search ─────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    source_type: Optional[str] = None   # optional filter by type


class SearchResult(BaseModel):
    chunk_text: str
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    score: float
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    answer: Optional[str] = None


# ── Upload / Ingestion ─────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    status: str                  # "success" or "error"
    filename: str
    source_id: Optional[int] = None
    chunks_stored: Optional[int] = None
    message: str


# ── GitHub Ingestion ───────────────────────────────────────────────────────────

class GithubIngestRequest(BaseModel):
    owner: str          # GitHub username or organisation (e.g. "octocat")
    repo: str           # Repository name (e.g. "Hello-World")
    token: Optional[str] = None  # Personal access token for private repos


class GithubIngestResponse(BaseModel):
    status: str                       # "success" or "error"
    repo: str                         # "owner/repo"
    source_id: Optional[int] = None
    files_processed: Optional[int] = None
    chunks_stored: Optional[int] = None
    message: str


# ── Sources ────────────────────────────────────────────────────────────────────

class SourceSchema(BaseModel):
    id: int
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    source_identifier: Optional[str] = None
    ingested_at: Optional[str] = None
    chunk_count: int = 0

    class Config:
        from_attributes = True


class SourcesListResponse(BaseModel):
    sources: List[SourceSchema]
    total: int


class DeleteResponse(BaseModel):
    status: str
    message: str
