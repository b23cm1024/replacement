from app.services.extractors.pdf_extractor import extract_pdf
from app.services.parsers.docling_parser import parse_docling

print("Starting...")

doc = extract_pdf(r"C:\Users\vamsi\OneDrive\Desktop\my_intern_placement_prep\ai-search-backend\test_files\offer_letter.pdf")

elements = parse_docling(doc)

print("Elements Count:", len(elements))

for element in elements[:15]:
    print(element)