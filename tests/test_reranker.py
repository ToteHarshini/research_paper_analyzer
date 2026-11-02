
from src.pdf_parser import extract_pdf_text
from src.chunker import chunk_pages
from src.bm25_search import create_bm25_index
from src.hybrid_retriever import hybrid_search
from src.reranker import rerank_results


PDF_PATH = "data/uploaded_pdfs/sample 2.pdf"


def main():
    # 1. Extract PDF text.
    pages = extract_pdf_text(PDF_PATH)

    # 2. Divide the PDF into chunks.
    chunks = chunk_pages(
        pages=pages,
        paper_id="PAPER01",
        paper_title="Sample Research Paper",
        chunk_size=1000,
        overlap=200
    )

    print("Chunks generated:", len(chunks))

    # 3. Create the BM25 index.
    index = create_bm25_index(chunks)

    # 4. Search using hybrid retrieval.
    query = "What attention mechanism does the Transformer use?"

    hybrid_results = hybrid_search(
        index=index,
        chunks=chunks,
        query=query,
        top_k=20
    )

    print("\nHybrid retrieval completed.")
    print("Candidate passages:", len(hybrid_results))

    # 5. Rerank the candidate passages.
    final_results = rerank_results(
        query=query,
        results=hybrid_results,
        top_k=5
    )

    # 6. Display the final results.
    print("\nRERANKED RESULTS")

    for rank, result in enumerate(final_results, start=1):
        chunk = result["chunk"]

        print(f"\nRank: {rank}")
        print("Chunk ID:", chunk["chunk_id"])
        print("Section:", chunk["section"])
        print("Page:", chunk["page_number"])
        print("RRF Score:", result["rrf_score"])
        print("Reranker Score:", result["reranker_score"])
        print("Text:", chunk["text"][:500])


if __name__ == "__main__":
    main()
