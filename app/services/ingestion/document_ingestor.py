import os
from dotenv import load_dotenv

load_dotenv()

from app.database import SessionLocal
from app.models.db_models import Source, DocumentChunk
from app.services.parsers.document_parser import parse_document
from app.services.vision.openai_vision import get_image_description
from app.services.chunkers.llm_chunker import llm_chunk_text
from app.services.embeddings.embedding_services import generate_embedding


def ingest_document(file_path: str, image_output_dir: str) -> dict:
    """
    End-to-end Universal Document Ingestion pipeline (PDF, DOCX, PPTX, XLSX).
    """

    db = SessionLocal()

    try:
        filename = os.path.basename(file_path)
        ext = filename.split(".")[-1].lower()
        print(f"\n{'='*60}")
        print(f"[Ingestor] Starting ingestion for: {filename} ({ext.upper()})")
        print(f"{'='*60}")

        # 1. Parse document & extract images
        print("[Ingestor] Step 1/5 - Extracting document structure and images with Docling...")
        elements, images_by_page = parse_document(file_path)
        
        # 2. Save images to disk and generate Vision descriptions
        print(f"[Ingestor] Step 2/5 - Processing images with Vision AI...")
        os.makedirs(image_output_dir, exist_ok=True)
        
        image_descriptions = {}
        
        for page_num, images in images_by_page.items():
            for idx, pil_img in enumerate(images):
                img_id = idx + 1
                
                # Save to disk
                img_filename = f"page_{page_num}_img_{img_id}.png"
                img_path = os.path.join(image_output_dir, img_filename)
                pil_img.save(img_path, format="PNG")
                
                print(f"[Ingestor]   -> Getting vision description for {img_filename}...")
                description = get_image_description(pil_img)
                
                placeholder = f"[IMAGE_FOUND_PAGE_{page_num}_{img_id}]"
                image_descriptions[placeholder] = f"\n\n[Embedded Image: {description}]\n\n"

        # 3. Compile full text, injecting image descriptions
        print("[Ingestor] Step 3/5 - Compiling text with embedded visual context...")
        full_text_lines = []
        for el in elements:
            if el.element_type == "image":
                # Replace the placeholder with the AI generated description
                desc = image_descriptions.get(el.content, "\n\n[Image without description]\n\n")
                full_text_lines.append(desc)
            elif el.element_type == "heading":
                full_text_lines.append(f"\n## {el.content}")
            else:
                full_text_lines.append(el.content)
                
        full_text = "\n".join(full_text_lines)

        # 4. LLM Semantic Chunking
        print("[Ingestor] Step 4/5 - Running LLM semantic chunker...")
        chunks = llm_chunk_text(full_text)
        print(f"[Ingestor]   -> {len(chunks)} chunk(s) produced.")

        if not chunks:
            raise ValueError("No chunks produced from the document. Check file content.")

        # 5. Store in Postgres
        print("[Ingestor] Step 5/5 - Embedding and storing chunks in database...")
        source = Source(
            source_type=ext,
            source_name=filename,
            source_identifier=file_path
        )
        db.add(source)
        db.commit()
        db.refresh(source)

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
        print(f"[Ingestor]   -> {len(chunks)} chunk(s) with embeddings stored.")
        print(f"[Ingestor] [SUCCESS] Ingestion complete for '{filename}'!")
        print(f"{'='*60}\n")

        return {
            "source_id": source.id,
            "chunks_stored": len(chunks),
            "filename": filename,
        }

    except Exception as e:
        db.rollback()
        print(f"[Ingestor] [ERROR] Error during ingestion: {e}")
        raise

    finally:
        db.close()
