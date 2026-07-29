from app.services.ingestion.pdf_ingestor import (
    ingest_pdf
)

ingest_pdf(
    r"C:\Users\vamsi\OneDrive\Desktop\my_intern_placement_prep\ai-search-backend\test_files\offer_letter.pdf",
    r"C:\Users\vamsi\OneDrive\Desktop\my_intern_placement_prep\ai-search-backend\storage\images"
)