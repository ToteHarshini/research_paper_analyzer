
from src.pdf_parser import extract_pdf_text
from src.chunker import chunk_pages
from src.vector_store import store_chunks, search_chunks


# Use the same PDF path that worked in test_chunker.py
PDF_PATH = "data/uploaded_pdfs/sample 2.pdf"


# ---------------------------------------
# STEP 1: EXTRACT PDF TEXT
# ---------------------------------------

pages = extract_pdf_text(PDF_PATH)

print("Pages extracted:", len(pages))


# ---------------------------------------
# STEP 2: GENERATE CHUNKS
# ---------------------------------------

chunks = chunk_pages(
    pages=pages,
    paper_id="PAPER01",
    paper_title="Sample Research Paper",
    chunk_size=1000,
    overlap=200
)

print("Chunks generated:", len(chunks))


# ---------------------------------------
# STEP 3: STORE CHUNKS
# ---------------------------------------

store_chunks(chunks)


# ---------------------------------------
# STEP 4: SEARCH THE DATABASE
# ---------------------------------------

question = "What is the methodology used in this research paper?"

results = search_chunks(
    query=question,
    n_results=3
)


# ---------------------------------------
# STEP 5: DISPLAY RESULTS
# ---------------------------------------

print("\nSEMANTIC SEARCH RESULTS\n")

for i in range(len(results["ids"][0])):

    print("=" * 60)

    print("Chunk ID:", results["ids"][0][i])

    print("Metadata:", results["metadatas"][0][i])

    print("Distance:", results["distances"][0][i])

    print("\nRetrieved text:")

    print(results["documents"][0][i])
