# inspect_doc.py

from app.services.extractors.pdf_extractor import extract_pdf

doc = extract_pdf(r"C:\Users\vamsi\OneDrive\Desktop\my_intern_placement_prep\ai-search-backend\test_files\offer_letter.pdf")

print(type(doc))
print(dir(doc))

print("Pictures Count:", len(doc.pictures))

print(doc.pictures)

print("Pages:", doc.num_pages)

for page in doc.pages:
    print(page)

print("Texts:", len(doc.texts))

for text in doc.texts[:10]:
    print(type(text))
    print(text)
    print("-" * 50)

picture = doc.pictures[0]

print("Meta:", picture.meta)
print("Captions:", picture.captions)
print("Caption Text:", picture.caption_text(doc))