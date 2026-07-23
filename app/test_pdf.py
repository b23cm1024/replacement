from services.extractors.pdf_extractor import extract_pdf

doc = extract_pdf(
    r"C:\Users\vamsi\OneDrive\Desktop\my_intern_placement_prep\ai-search-backend\test_files\offer_letter.pdf"
)

print(doc.export_to_markdown())