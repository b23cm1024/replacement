import fitz
import os


def extract_images(pdf_path, output_dir):

    os.makedirs(output_dir, exist_ok=True)

    pdf = fitz.open(pdf_path)

    extracted_images = []

    for page_index in range(len(pdf)):

        page = pdf[page_index]

        images = page.get_images(full=True)

        for image_index, img in enumerate(images):

            try:

                xref = img[0]

                base_image = pdf.extract_image(xref)

                image_bytes = base_image["image"]

                image_ext = base_image["ext"]

                width = base_image["width"]
                height = base_image["height"]

                image_area = width * height

                # Skip tiny decorative images/icons
                if width < 80 or height < 80:
                    continue

                # Skip very small overall area
                if image_area < 10000:
                    continue

                image_name = (
                    f"page_{page_index + 1}_img_{image_index + 1}.{image_ext}"
                )

                image_path = os.path.join(
                    output_dir,
                    image_name
                )

                with open(image_path, "wb") as image_file:
                    image_file.write(image_bytes)

                extracted_images.append(
                    {
                        "page_number": page_index + 1,
                        "image_path": image_path,
                        "width": width,
                        "height": height
                    }
                )

                print(
                    f"Saved: {image_name} | "
                    f"{width}x{height}"
                )

            except Exception as e:

                print(
                    f"Failed image on page "
                    f"{page_index + 1}: {e}"
                )

    pdf.close()

    return extracted_images