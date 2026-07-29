from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.db_models import DocumentChunk, Source
from app.services.embeddings.embedding_services import generate_embedding
from app.services.retrieval.reranker import rerank_chunks

def search_documents(query: str, db: Session, top_k: int = 5, source_type: str = None):
    """
    Performs a hybrid search (Dense Vector + Exact Match Fallback) 
    and re-ranks the top candidates using a Cross-Encoder.
    Optionally filters by source_type (e.g. "pdf", "github", "docx").
    """
    # 1. Generate Query Embedding
    query_vector = generate_embedding(query)
    
    # 2. Vector Search (Top 30 candidates)
    vector_query = db.query(DocumentChunk, Source).join(
        Source, DocumentChunk.source_id == Source.id
    )
    if source_type:
        vector_query = vector_query.filter(Source.source_type == source_type)
    vector_results = vector_query.order_by(
        DocumentChunk.embedding.cosine_distance(query_vector)
    ).limit(30).all()

    
    candidate_chunks = {}
    for chunk, source in vector_results:
        candidate_chunks[chunk.id] = {
            'id': chunk.id,
            'chunk_text': chunk.chunk_text,
            'source_name': source.source_name,
            'source_type': source.source_type,
            'metadata': chunk.chunk_metadata,
            'score': 0.0 # Will be overwritten by reranker
        }
        
    # 3. Exact Keyword Match Fallback (Top 10)
    # This ensures if the user types an exact keyword/acronym that the 
    # vector model misses, we still include it in the candidate pool for the reranker.
    keyword_query = db.query(DocumentChunk, Source).join(
        Source, DocumentChunk.source_id == Source.id
    ).filter(
        DocumentChunk.chunk_text.ilike(f"%{query}%")
    )
    if source_type:
        keyword_query = keyword_query.filter(Source.source_type == source_type)
    keyword_results = keyword_query.limit(10).all()

    
    for chunk, source in keyword_results:
        if chunk.id not in candidate_chunks:
            candidate_chunks[chunk.id] = {
                'id': chunk.id,
                'chunk_text': chunk.chunk_text,
                'source_name': source.source_name,
                'source_type': source.source_type,
                'metadata': chunk.chunk_metadata,
                'score': 0.0
            }
            
    # Convert dict to list
    candidates_list = list(candidate_chunks.values())
    
    if not candidates_list:
        return []
        
    # 4. Reranking using Cross-Encoder
    final_results = rerank_chunks(query, candidates_list, top_k=top_k)
    
    # Format output
    return [
        {
            "chunk_text": res["chunk_text"],
            "source_name": res["source_name"],
            "source_type": res["source_type"],
            "metadata": res.get("metadata", {}),
            "score": res.get("rerank_score", 0.0)
        }
        for res in final_results
    ]
