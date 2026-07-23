from sentence_transformers import CrossEncoder

# Load a lightweight, highly accurate cross-encoder model for re-ranking
try:
    reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
except Exception as e:
    print(f"Warning: Failed to load reranker model. Error: {e}")
    reranker_model = None

def rerank_chunks(query: str, chunks: list, top_k: int = 5):
    """
    Reranks a list of candidate chunks based on the query.
    chunks is expected to be a list of dictionaries, e.g.:
    [{'chunk_text': '...', 'source_name': '...', 'id': 1}, ...]
    """
    if not reranker_model or not chunks:
        # Fallback to returning original chunks if model isn't loaded or no chunks
        return chunks[:top_k]
    
    # Create pairs of (query, chunk_text)
    pairs = [[query, chunk['chunk_text']] for chunk in chunks]
    
    # Predict relevance scores
    scores = reranker_model.predict(pairs)
    
    # Attach scores to chunks
    for chunk, score in zip(chunks, scores):
        chunk['rerank_score'] = float(score)
        
    # Sort by descending score
    ranked_chunks = sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)
    
    return ranked_chunks[:top_k]
