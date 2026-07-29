from sentence_transformers import SentenceTransformer

# Lazy-loaded model: initialized on first use to avoid slow startup times
# and prevent loading the model even if embeddings are never called.
_model = None


def _get_model() -> SentenceTransformer:
    """Returns the embedding model, initializing it on first call."""
    global _model
    if _model is None:
        print("[Embeddings] Loading SentenceTransformer model (first use)...")
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        print("[Embeddings] Model loaded successfully.")
    return _model


def generate_embedding(text: str) -> list:
    model = _get_model()
    embedding = model.encode(
        text,
        normalize_embeddings=True
    )
    return embedding.tolist()