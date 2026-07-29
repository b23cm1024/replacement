"""
GitHub Repository Ingestor
---------------------------
Full pipeline: GitHub Repo -> Fetch Files -> Code Chunking
           -> Embedding -> PostgreSQL (pgvector) storage.

This mirrors pdf_ingestor.py exactly in structure and storage format.
GitHub chunks use source_type="github" in the sources table so retrieval
can identify them. The existing /search endpoint automatically searches
both PDF and GitHub chunks since they share the document_chunks table.

Entry point: ingest_github_repo(owner, repo) -> dict
"""

import os
from dotenv import load_dotenv

load_dotenv()

from app.database import SessionLocal
from app.models.db_models import Source, DocumentChunk
from app.services.github.github_client import get_all_repo_files
from app.services.chunkers.code_chunker import chunk_code_file
from app.services.embeddings.embedding_services import generate_embedding


def ingest_github_repo(owner: str, repo: str, token: str = None) -> dict:
    """
    End-to-end GitHub repository ingestion pipeline.

    Args:
        owner: GitHub username or org (e.g. "octocat")
        repo:  Repository name (e.g. "Hello-World")

    Returns:
        Summary dict:
        {
            "source_id":       int,
            "files_processed": int,
            "chunks_stored":   int,
            "repo":            "owner/repo"
        }

    Raises:
        Exception on unrecoverable failure (caller should handle and respond 500).
    """
    db = SessionLocal()
    repo_full = f"{owner}/{repo}"

    try:
        print(f"\n{'='*60}")
        print(f"[GitHub Ingestor] Starting ingestion for: {repo_full}")
        print(f"{'='*60}")

        # ── Step 1: Fetch all code files from GitHub ──────────────────────────
        print("[GitHub Ingestor] Step 1/4 — Fetching files from GitHub API...")
        files = get_all_repo_files(owner, repo, token=token)
        print(f"[GitHub Ingestor]   -> {len(files)} files fetched.")

        if not files:
            raise ValueError(
                f"No supported code files found in '{repo_full}'. "
                "Make sure the repo is public or GITHUB_TOKEN is set."
            )

        # ── Step 2: Create source record ──────────────────────────────────────
        print("[GitHub Ingestor] Step 2/4 — Creating source record in database...")
        source = Source(
            source_type="github",
            source_name=repo_full,
            source_identifier=f"https://github.com/{repo_full}",
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        print(f"[GitHub Ingestor]   -> Source record created (ID: {source.id})")

        # ── Step 3: Chunk each file + generate embeddings ─────────────────────
        print("[GitHub Ingestor] Step 3/4 — Chunking files and generating embeddings...")
        total_chunks = 0
        files_with_chunks = 0

        for file in files:
            # Pass the repo name into file metadata for traceability
            file["repo"] = repo_full

            chunks = chunk_code_file(file)
            if not chunks:
                continue

            files_with_chunks += 1

            for index, chunk in enumerate(chunks):
                embedding = generate_embedding(chunk.content)

                db_chunk = DocumentChunk(
                    source_id=source.id,
                    chunk_title=chunk.title,
                    chunk_text=chunk.content,
                    chunk_index=index,
                    chunk_metadata={
                        **chunk.metadata,
                        "file_name": file["name"],
                        "chunk_index_in_file": index,
                    },
                    embedding=embedding,
                )
                db.add(db_chunk)
                total_chunks += 1

        db.commit()
        print(f"[GitHub Ingestor]   -> {total_chunks} chunks stored from {files_with_chunks} files.")

        # ── Step 4: Summary ───────────────────────────────────────────────────
        print(f"[GitHub Ingestor] Step 4/4 — Done!")
        print(f"[GitHub Ingestor] Repo '{repo_full}' ingested successfully.")
        print(f"{'='*60}\n")

        return {
            "source_id":       source.id,
            "files_processed": files_with_chunks,
            "chunks_stored":   total_chunks,
            "repo":            repo_full,
        }

    except Exception as e:
        db.rollback()
        print(f"[GitHub Ingestor] ERROR during ingestion of '{repo_full}': {e}")
        raise

    finally:
        db.close()
