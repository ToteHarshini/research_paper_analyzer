
import pymupdf

def extract_pdf_text(pdf_path):

    # Open the PDF
    doc = pymupdf.open(pdf_path)

    # Store extracted pages
    pages = []

    # Iterate through every page
    for page_number, page in enumerate(doc, start=1):

        # Extract text
        text = page.get_text("text")

        # Store page number and text
        pages.append({
            "page": page_number,
            "text": text
        })

    doc.close()

    return pages