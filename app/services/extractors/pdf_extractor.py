from docling.document_converter import DocumentConverter


def extract_pdf(pdf_path):
    converter = DocumentConverter()

    result = converter.convert(pdf_path)

    return result.document