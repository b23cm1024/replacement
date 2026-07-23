from app.models.document_element import DocumentElement


def parse_docling(doc):

    elements = []

    # Process text items
    for item in doc.texts:

        # Skip text that belongs to images/logos
        if item.parent and item.parent.cref.startswith("#/pictures/"):
            continue

        page_number = None

        if item.prov:
            page_number = item.prov[0].page_no

        item_type = type(item).__name__

        # Heading
        if item_type == "SectionHeaderItem":

            elements.append(
                DocumentElement(
                    element_type="heading",
                    content=item.text,
                    metadata={
                        "page_number": page_number,
                        "heading_level": getattr(item, "level", None)
                    }
                )
            )

        # Email
        elif getattr(item, "hyperlink", None):

            elements.append(
                DocumentElement(
                    element_type="email",
                    content=item.text,
                    metadata={
                        "page_number": page_number,
                        "hyperlink": str(item.hyperlink)
                    }
                )
            )

        # Form Field
        elif "_" * 10 in item.text:

            elements.append(
                DocumentElement(
                    element_type="form_field",
                    content=item.text,
                    metadata={
                        "page_number": page_number
                    }
                )
            )

        # Paragraph
        else:

            elements.append(
                DocumentElement(
                    element_type="paragraph",
                    content=item.text,
                    metadata={
                        "page_number": page_number
                    }
                )
            )

    # Process Images
    for picture in doc.pictures:

        page_number = None

        if picture.prov:
            page_number = picture.prov[0].page_no

        elements.append(
            DocumentElement(
                element_type="image",
                content="[IMAGE_FOUND]",
                metadata={
                    "page_number": page_number,
                    "image_path": "",
                    "image_description": "",
                    "image_type": "unknown"
                }
            )
        )

    return elements