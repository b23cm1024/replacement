from app.services.extractors.pdf_extractor import extract_pdf
from app.services.extractors.image_extractor import extract_images
from app.services.chunkers.pdf_chunker import build_chunks
from app.services.embeddings.embedding_services import generate_embedding


doc = extract_pdf(
    r"C:\Users\vamsi\OneDrive\Desktop\my_intern_placement_prep\ai-search-backend\test_files\offer_letter.pdf"
)

images = extract_images(
    r"C:\Users\vamsi\OneDrive\Desktop\my_intern_placement_prep\ai-search-backend\test_files\offer_letter.pdf",
    r"C:\Users\vamsi\OneDrive\Desktop\my_intern_placement_prep\ai-search-backend\storage\images"
)

chunks = build_chunks(
    doc,
    images
)

for chunk in chunks:

    vector = generate_embedding(
        chunk.content
    )

    print(
        chunk.title,
        len(vector)
    )