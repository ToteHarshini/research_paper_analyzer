
from src.pdf_parser import extract_pdf_text
from src.chunker import chunk_pages
from src.bm25_search import create_bm25_index, search_bm25

PDF_PATH = "data/uploaded_pdfs/sample 2.pdf"

# Step 1: Extract PDF pages
pages = extract_pdf_text(PDF_PATH)

# Step 2: Generate chunks
chunks = chunk_pages(
    pages=pages,
    paper_id="PAPER01",
    paper_title="Sample Research Paper",
    chunk_size=1000,
    overlap=200
)

print("Chunks generated:", len(chunks))

# Step 3: Create BM25 index
index = create_bm25_index(chunks)

print("BM25 index created successfully!")

# Step 4: Search
query = "What is the attention mechanism used in the Transformer?"

results = search_bm25(index, chunks, query, top_k=5)

# Step 5: Display results
print("\nBM25 SEARCH RESULTS\n")

for chunk, score in results:
    print("=" * 60)
    print("Chunk ID:", chunk["chunk_id"])
    print("Section:", chunk["section"])
    print("Page:", chunk["page_number"])
    print("BM25 Score:", score)
    print("\nRetrieved Text:")
    print(chunk["text"])