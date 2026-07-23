from app.models.chunk import Chunk

MAX_CHARS = 1000


def create_chunk(
    title,
    content,
    page_number,
    page_images
):

    chunks = []

    content = "\n".join(content)

    if len(content) <= MAX_CHARS:

        chunks.append(
            Chunk(
                title=title,
                content=content,
                metadata={
                    "page_number": page_number,
                    "images": page_images
                }
            )
        )

        return chunks

    start = 0
    part = 1

    while start < len(content):

        end = start + MAX_CHARS

        chunk_text = content[start:end]

        chunks.append(
            Chunk(
                title=f"{title} (Part {part})",
                content=chunk_text,
                metadata={
                    "page_number": page_number,
                    "images": page_images
                }
            )
        )

        start = end
        part += 1

    return chunks


def build_chunks(doc, images):

    chunks = []

    images_by_page = {}

    for image in images:

        page = image["page_number"]

        if page not in images_by_page:
            images_by_page[page] = []

        images_by_page[page].append(
            image["image_path"]
        )

    current_title = None
    current_content = []
    current_page = None

    skip_titles = {
        "UNITED TECHLAB SOLUTION PRIVATE LIMITED",
        "Non-Disclosure Agreement (NDA)"
    }

    for item in doc.texts:

        # Skip OCR text inside logos/images
        if (
            item.parent
            and hasattr(item.parent, "cref")
            and item.parent.cref.startswith("#/pictures/")
        ):
            continue

        item_text = item.text.strip()

        if not item_text:
            continue

        page_number = None

        if item.prov:
            page_number = item.prov[0].page_no

        # Skip footer page numbers
        if item_text.isdigit():
            continue

        label = str(
            getattr(item, "label", "")
        )

        if "PAGE_FOOTER" in label:
            continue

        item_type = type(item).__name__

        if item_type == "SectionHeaderItem":

            if item_text in skip_titles:
                continue

            if item_text == "The Intern agrees to:":

                current_content.append(
                    item_text
                )

                continue

            if current_title and current_content:

                chunks.extend(
                    create_chunk(
                        current_title,
                        current_content,
                        current_page,
                        images_by_page.get(
                            current_page,
                            []
                        )
                    )
                )

            current_title = item_text
            current_content = []
            current_page = page_number

        else:

            current_content.append(
                item_text
            )

    if current_title and current_content:

        chunks.extend(
            create_chunk(
                current_title,
                current_content,
                current_page,
                images_by_page.get(
                    current_page,
                    []
                )
            )
        )

    return chunks