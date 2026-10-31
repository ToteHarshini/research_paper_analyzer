

from src.pdf_parser import extract_pdf_text
from src.chunker import chunk_pages


PDF_PATH = "data/uploaded_pdfs/sample 2.pdf"


# Step 1: Extract text from PDF
pages = extract_pdf_text(PDF_PATH)

# Step 2: Generate chunks
chunks = chunk_pages(
    pages=pages,
    paper_id="PAPER01",
    paper_title="Sample Research Paper",
    chunk_size=1000,
    overlap=200
)

# Step 3: Display results
print("Total pages:", len(pages))
print("Total chunks:", len(chunks))

print("\nFIRST 3 CHUNKS\n")

for chunk in chunks[:3]:

    print("=" * 60)

    print("Chunk ID:", chunk["chunk_id"])
    print("Paper ID:", chunk["paper_id"])
    print("Paper:", chunk["paper_title"])
    print("Section:", chunk["section"])
    print("Page:", chunk["page_number"])

    print("\nText:")
    print(chunk["text"])
