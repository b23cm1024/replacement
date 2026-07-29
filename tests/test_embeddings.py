from app.services.embeddings.embedding_services import (
    generate_embedding
)


text = """
The purpose of this Agreement is to protect
the confidential information.
"""

embedding = generate_embedding(text)

print("Dimension:", len(embedding))

print("First 10 Values:")
print(embedding[:10])