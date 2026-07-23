from pydantic import BaseModel
from typing import List, Optional


# ── Search ─────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    chunk_text: str
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    score: float


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


class GithubIngestResponse(BaseModel):
    status: str                       # "success" or "error"
    repo: str                         # "owner/repo"
    source_id: Optional[int] = None
    files_processed: Optional[int] = None
    chunks_stored: Optional[int] = None
    message: str
