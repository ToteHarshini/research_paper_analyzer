
from src.pdf_parser import extract_pdf_text
from src.chunker import chunk_pages
from src.bm25_search import create_bm25_index
from src.hybrid_retriever import hybrid_search


PDF_PATH = "data/uploaded_pdfs/sample 2.pdf"

# Step 1: Extract PDF text
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

print("BM25 index created!")

# Step 4: Perform hybrid search
query = "What attention mechanism does the Transformer use?"

results = hybrid_search(
    index=index,
    chunks=chunks,
    query=query,
    top_k=5
)

# Step 5: Display results
print("\nHYBRID SEARCH RESULTS\n")

for result in results:

    chunk = result["chunk"]

    print("=" * 60)
    print("Chunk ID:", chunk["chunk_id"])
    print("Section:", chunk["section"])
    print("Page:", chunk["page_number"])
    print("RRF Score:", result["rrf_score"])
    print("Individual rankings:", result["rankings"])
    print("\nRetrieved Text:")
    print(chunk["text"])
