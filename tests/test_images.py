from app.services.extractors.image_extractor import extract_images


images = extract_images(
    r"C:\Users\vamsi\OneDrive\Desktop\my_intern_placement_prep\ai-search-backend\test_files\offer_letter.pdf",
    r"C:\Users\vamsi\OneDrive\Desktop\my_intern_placement_prep\ai-search-backend\storage\images"
)

print("Images Found:", len(images))

for image in images:
    print(image)