"""
PDF Ingestor
------------
Full pipeline: PDF → Text Extraction → Image Extraction → LLM Chunking
             → Embedding → PostgreSQL (pgvector) storage.

Files are retained permanently on the server under:
  storage/uploads/<filename>.pdf
  storage/images/<doc_name>/<page>_img_*.ext

This module is the single entry point to take a PDF from disk and make it
fully queryable via the /search endpoint.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from app.database import SessionLocal
from app.models.db_models import Source, DocumentChunk
from app.services.extractors.pdf_extractor import extract_pdf
from app.services.extractors.image_extractor import extract_images
from app.services.chunkers.llm_chunker import llm_chunk_text
from app.services.embeddings.embedding_services import generate_embedding


def _extract_full_text(doc) -> str:
    """
    Converts the docling document object into a single plain-text string.
    We concatenate all text items in document order, separated by newlines,
    so the LLM chunker receives a clean, readable representation.
    """
    lines = []

    for item in doc.texts:

        # Skip text embedded inside image/logo regions
        if (
            item.parent
            and hasattr(item.parent, "cref")
            and item.parent.cref.startswith("#/pictures/")
        ):
            continue

        item_text = item.text.strip()

        if not item_text:
            continue

        # Skip standalone page numbers
        if item_text.isdigit():
            continue

        label = str(getattr(item, "label", ""))
        if "PAGE_FOOTER" in label or "PAGE_HEADER" in label:
            continue

        item_type = type(item).__name__

        # Add a blank line before headings to give the LLM a structural cue
        if item_type == "SectionHeaderItem":
            lines.append("")
            lines.append(f"## {item_text}")
        else:
            lines.append(item_text)

    return "\n".join(lines)


def ingest_pdf(pdf_path: str, image_output_dir: str) -> dict:
    """
    End-to-end PDF ingestion pipeline.

    Args:
        pdf_path: Absolute path to the PDF file on disk.
        image_output_dir: Directory to save extracted images. Created if absent.

    Returns:
        A summary dict: {"source_id": int, "chunks_stored": int, "filename": str}

    Raises:
        Exception on any unrecoverable failure (caller should handle and respond 500).
    """

    db = SessionLocal()

    try:
        filename = os.path.basename(pdf_path)
        print(f"\n{'='*60}")
        print(f"[Ingestor] Starting ingestion for: {filename}")
        print(f"{'='*60}")

        # ── Step 1: Extract structured document from PDF via docling ──────────
        print("[Ingestor] Step 1/5 — Extracting PDF structure with Docling...")
        doc = extract_pdf(pdf_path)

        # ── Step 2: Extract images and save to server ─────────────────────────
        print("[Ingestor] Step 2/5 — Extracting embedded images...")
        images = extract_images(pdf_path, image_output_dir)
        print(f"[Ingestor]   └─ {len(images)} image(s) saved to {image_output_dir}")

        # Build a lookup: {page_number: [image_paths]}
        images_by_page = {}
        for img in images:
            page = img["page_number"]
            images_by_page.setdefault(page, []).append(img["image_path"])

        # ── Step 3: Convert docling doc to plain text for LLM chunking ────────
        print("[Ingestor] Step 3/5 — Converting document to plain text...")
        full_text = _extract_full_text(doc)
        print(f"[Ingestor]   └─ {len(full_text)} characters extracted.")

        # ── Step 4: LLM-based semantic chunking ───────────────────────────────
        print("[Ingestor] Step 4/5 — Running LLM semantic chunker...")
        chunks = llm_chunk_text(full_text, page_images=images_by_page)
        print(f"[Ingestor]   └─ {len(chunks)} chunk(s) produced.")

        if not chunks:
            raise ValueError("No chunks produced from the document. Check PDF content.")

        # ── Step 5: Store source + chunks + embeddings in PostgreSQL ──────────
        print("[Ingestor] Step 5/5 — Embedding and storing chunks in database...")

        source = Source(
            source_type="pdf",
            source_name=filename,
            source_identifier=pdf_path  # full path retained on server
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        print(f"[Ingestor]   └─ Source record created (ID: {source.id})")

        for index, chunk in enumerate(chunks):
            embedding = generate_embedding(chunk.content)

            db_chunk = DocumentChunk(
                source_id=source.id,
                chunk_title=chunk.title,
                chunk_text=chunk.content,
                chunk_index=index,
                chunk_metadata=chunk.metadata,
                embedding=embedding
            )
            db.add(db_chunk)

        db.commit()
        print(f"[Ingestor]   └─ {len(chunks)} chunk(s) with embeddings stored.")

        print(f"[Ingestor] ✅ Ingestion complete for '{filename}'!")
        print(f"{'='*60}\n")

        return {
            "source_id": source.id,
            "chunks_stored": len(chunks),
            "filename": filename,
        }

    except Exception as e:
        db.rollback()
        print(f"[Ingestor] ❌ Error during ingestion: {e}")
        raise

    finally:
        db.close()