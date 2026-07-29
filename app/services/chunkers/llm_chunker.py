"""
LLM-Based Semantic Chunker
--------------------------
Strategy: Agentic Chunking (Proposition-Based)
- The entire extracted document text is passed to an LLM (Groq/Llama) in one shot.
- The LLM is instructed to identify logical semantic sections and return them as
  a structured JSON list of {"title": "...", "content": "..."} objects.
- Each returned object becomes a single Chunk — meaning the LLM does the chunking
  intelligently based on meaning, not arbitrary character limits.

Why this approach:
- Avoids mid-sentence/mid-thought cuts from naive character splitting.
- Keeps related facts together (e.g. a clause in a contract, a financial figure
  with its context, a full job responsibility).
- The model can handle irregular document structures (PDFs with tables, mixed
  headers, bullet points) much better than regex-based approaches.
"""

import os
import json
from openai import OpenAI
from app.models.chunk import Chunk

# Reuse the same Groq client (OpenAI-compatible) used by generation_service
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
    return _client


SYSTEM_PROMPT = """You are a document intelligence assistant.

Your job is to read a raw document text extracted from a PDF and split it into
semantically meaningful chunks. Each chunk must represent ONE complete idea,
clause, section, or topic — similar to how a human expert would divide a document
into logical reading units.

Rules:
1. Group content that belongs to the same topic/clause together into a single chunk.
2. Do NOT split a single idea or clause across multiple chunks.
3. Each chunk must have a short, descriptive title (max 10 words).
4. Chunks should be self-contained — a reader should understand the chunk without
   needing to read adjacent chunks.
5. Keep chunk sizes between 100 and 800 words. If a section is too long, split it
   at a logical boundary (e.g. sub-topic, new point).
6. Return your response as a valid JSON array only. No extra text, no markdown code
   fences — just the raw JSON array.

Output format:
[
  {"title": "Short descriptive title", "content": "Full text of this chunk..."},
  {"title": "Another title", "content": "..."},
  ...
]"""


def llm_chunk_text(full_text: str, page_images: dict = None) -> list[Chunk]:
    """
    Given the full extracted text of a document, asks the LLM to semantically
    chunk it and returns a list of Chunk objects.

    Args:
        full_text: The raw text extracted from the PDF.
        page_images: Optional dict of {page_number: [image_paths]} to attach
                     image metadata to chunks where possible.

    Returns:
        A list of Chunk dataclass instances ready for embedding and storage.
    """
    if not full_text or not full_text.strip():
        print("[LLM Chunker] Empty document text. Nothing to chunk.")
        return []

    if not os.getenv("GROQ_API_KEY"):
        print("[LLM Chunker] GROQ_API_KEY not set. Falling back to rule-based chunking.")
        return _fallback_chunk(full_text)

    client = _get_client()

    # Groq's context window is large enough for most PDFs.
    # We truncate at ~12000 words as a safe upper limit.
    words = full_text.split()
    if len(words) > 12000:
        print(f"[LLM Chunker] Document too long ({len(words)} words). Truncating to 12000 words.")
        full_text = " ".join(words[:12000])

    print(f"[LLM Chunker] Sending {len(full_text)} characters to LLM for chunking...")

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Document text:\n\n{full_text}"}
            ],
            temperature=0.0,
            max_tokens=8000,
        )

        raw_output = response.choices[0].message.content.strip()

        # Strip markdown code fences if the model added them anyway
        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1]
            if raw_output.startswith("json"):
                raw_output = raw_output[4:]
            raw_output = raw_output.strip()
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3].strip()

        chunk_dicts = json.loads(raw_output)

        chunks = []
        for item in chunk_dicts:
            title = item.get("title", "Untitled Section").strip()
            content = item.get("content", "").strip()
            if not content:
                continue
            chunks.append(
                Chunk(
                    title=title,
                    content=content,
                    metadata={
                        "chunking_method": "llm_semantic",
                        "images": []  # Images are attached at ingestor level if needed
                    }
                )
            )

        print(f"[LLM Chunker] LLM produced {len(chunks)} semantic chunks.")
        return chunks

    except json.JSONDecodeError as e:
        print(f"[LLM Chunker] JSON parse failed: {e}. Falling back to rule-based chunking.")
        return _fallback_chunk(full_text)

    except Exception as e:
        print(f"[LLM Chunker] LLM call failed: {e}. Falling back to rule-based chunking.")
        return _fallback_chunk(full_text)


def _fallback_chunk(text: str, max_chars: int = 800) -> list[Chunk]:
    """
    Simple paragraph-based fallback chunker used when the LLM is unavailable.
    Splits on double newlines and groups into chunks up to max_chars.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    buffer = []
    buffer_len = 0
    part = 1

    for para in paragraphs:
        if buffer_len + len(para) > max_chars and buffer:
            chunks.append(
                Chunk(
                    title=f"Section {part}",
                    content="\n\n".join(buffer),
                    metadata={"chunking_method": "fallback_paragraph", "images": []}
                )
            )
            buffer = []
            buffer_len = 0
            part += 1
        buffer.append(para)
        buffer_len += len(para)

    if buffer:
        chunks.append(
            Chunk(
                title=f"Section {part}",
                content="\n\n".join(buffer),
                metadata={"chunking_method": "fallback_paragraph", "images": []}
            )
        )

    print(f"[Fallback Chunker] Produced {len(chunks)} paragraph-based chunks.")
    return chunks
