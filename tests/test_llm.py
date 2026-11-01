from src.pdf_parser import extract_pdf_text
from src.chunker import chunk_pages
from src.bm25_search import create_bm25_index
from src.hybrid_retriever import hybrid_search
from src.reranker import rerank_results
from src.llm import generate_research_report

PDF_PATH = "data/uploaded_pdfs/sample 2.pdf"

# 1. Extract PDF text
pages = extract_pdf_text(PDF_PATH)
print("Pages extracted:", len(pages))

# 2. Create chunks
chunks = chunk_pages(
    pages=pages,
    paper_id="PAPER01",
    paper_title="Sample Research Paper",
    chunk_size=1000,
    overlap=200
)
print("Chunks generated:", len(chunks))

# 3. Create BM25 index
index = create_bm25_index(chunks)

# 4. Hybrid retrieval
query = "What attention mechanism does the Transformer use?"

hybrid_results = hybrid_search(
    index=index,
    chunks=chunks,
    query=query,
    top_k=20
)
print("Hybrid retrieval completed:", len(hybrid_results))

# 5. Rerank results
reranked_results = rerank_results(
    query=query,
    results=hybrid_results,
    top_k=5
)
print("Reranking completed:", len(reranked_results))

# 6. Generate report using Gemini
print("\nSending evidence to Gemini...")

report = generate_research_report(
    question=query,
    results=reranked_results
)

print("\n" + "=" * 60)
print("RESEARCH REPORT")
print("=" * 60)
print(report)