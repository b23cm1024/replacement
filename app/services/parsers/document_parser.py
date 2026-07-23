import os
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption, PowerpointFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from app.models.document_element import DocumentElement


def parse_document(file_path: str):
    """
    Parses a document (PDF, DOCX, PPTX, XLSX, etc.) into structured DocumentElements.
    Automatically extracts PIL images from the document if they meet size criteria.
    
    Returns:
        tuple: (elements, images_by_page)
        - elements: list of DocumentElement objects.
        - images_by_page: dict mapping page_number -> list of PIL.Image objects.
    """
    
    # Enable image extraction for all major formats
    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True
    
    converter = DocumentConverter(
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.DOCX,
            InputFormat.PPTX,
            InputFormat.XLSX,
            InputFormat.MD,
            InputFormat.HTML
        ],
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
            InputFormat.DOCX: WordFormatOption(pipeline_options=pipeline_options),
            InputFormat.PPTX: PowerpointFormatOption(pipeline_options=pipeline_options),
        }
    )

    result = converter.convert(file_path)
    doc = result.document
    
    elements = []
    images_by_page = {}

    # Process text items
    for item in doc.texts:
        # Skip text that belongs to images/logos
        if item.parent and hasattr(item.parent, "cref") and item.parent.cref.startswith("#/pictures/"):
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
                    metadata={"page_number": page_number, "heading_level": getattr(item, "level", None)}
                )
            )
        # Email
        elif getattr(item, "hyperlink", None):
            elements.append(
                DocumentElement(
                    element_type="email",
                    content=item.text,
                    metadata={"page_number": page_number, "hyperlink": str(item.hyperlink)}
                )
            )
        # Form Field
        elif "_" * 10 in item.text:
            elements.append(
                DocumentElement(
                    element_type="form_field",
                    content=item.text,
                    metadata={"page_number": page_number}
                )
            )
        # Paragraph
        else:
            elements.append(
                DocumentElement(
                    element_type="paragraph",
                    content=item.text,
                    metadata={"page_number": page_number}
                )
            )

    # Process Tables
    for table in getattr(doc, 'tables', []):
        page_number = None
        if table.prov:
            page_number = table.prov[0].page_no
        
        try:
            # We pass doc=doc because using export_to_markdown without doc is deprecated
            md_table = table.export_to_markdown()
            elements.append(
                DocumentElement(
                    element_type="table",
                    content=md_table,
                    metadata={"page_number": page_number}
                )
            )
        except Exception as e:
            print(f"Warning: Failed to export table to markdown: {e}")

    # Process Images
    for picture_index, picture in enumerate(doc.pictures):
        page_number = None
        if picture.prov:
            page_number = picture.prov[0].page_no
        
        # Fallback to page 1 if no provenance
        if page_number is None:
            page_number = 1
            
        pil_image = None
        if hasattr(picture, "image") and picture.image:
            if hasattr(picture.image, "pil_image") and picture.image.pil_image:
                pil_image = picture.image.pil_image
                
                # Check dimensions to skip tiny icons
                w, h = pil_image.size
                if w < 80 or h < 80 or (w * h) < 10000:
                    continue
        
        if pil_image:
            if page_number not in images_by_page:
                images_by_page[page_number] = []
            images_by_page[page_number].append(pil_image)

            # We insert an [IMAGE_FOUND_X] placeholder so the text converter knows where it is
            img_id = len(images_by_page[page_number])
            
            elements.append(
                DocumentElement(
                    element_type="image",
                    content=f"[IMAGE_FOUND_PAGE_{page_number}_{img_id}]",
                    metadata={
                        "page_number": page_number,
                        "image_index": img_id
                    }
                )
            )

    return elements, images_by_page
