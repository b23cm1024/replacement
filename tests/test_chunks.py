from app.services.extractors.pdf_extractor import extract_pdf
from app.services.extractors.image_extractor import extract_images
from app.services.chunkers.pdf_chunker import build_chunks


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

print("Chunks:", len(chunks))

for chunk in chunks:

    print("\n" + "=" * 50)

    print("TITLE:")
    print(chunk.title)

    print("\nPAGE:")
    print(chunk.metadata["page_number"])

    print("\nIMAGES:")
    print(chunk.metadata["images"])

    print("\nCONTENT:")
    print(chunk.content[:300])