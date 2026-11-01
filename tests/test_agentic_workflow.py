
from pathlib import Path

from src.pdf_parser import extract_pdf_text
from src.chunker import chunk_pages
from src.bm25_search import create_bm25_index
from src.vector_store import store_chunks
from src.research_workflow import run_agentic_research


def main():

    # 1. Locate the sample PDF
    project_root = Path(__file__).resolve().parents[1]
    pdf_path = project_root / "data" / "uploaded_pdfs" / "sample 2.pdf"

    if not pdf_path.exists():
        raise FileNotFoundError(f"Sample PDF not found: {pdf_path}")

    # 2. Extract PDF text
    print("\n--- PDF PARSING ---")

    pages = extract_pdf_text(str(pdf_path))

    print(f"Extracted {len(pages)} pages.")

    print("\n--- DEBUGGING PDF TEXT ---")

    for page in pages[:3]:
        print("Page:", page["page"])
        print("Text length:", len(page["text"]))
        print("First 200 characters:", repr(page["text"][:200]))
    # 3. Generate chunks
    print("\n--- CHUNKING ---")

    chunks = chunk_pages(
        pages=pages,
        paper_id="PAPER01",
        paper_title="Sample Research Paper",
        chunk_size=1000,
        overlap=200
    )

    print(f"Generated {len(chunks)} chunks.")

    # 4. Create BM25 index
    print("\n--- CREATING BM25 INDEX ---")

    index = create_bm25_index(chunks)

    print("BM25 index created.")

    # 5. Store chunks in ChromaDB
    print("\n--- STORING VECTORS ---")

    store_chunks(chunks)

    print("Chunks stored successfully.")

    # 6. Run the agentic workflow
    question = (
        "Explain the Transformer architecture, "
        "its attention mechanisms, and its limitations."
    )

    print("\n--- RUNNING AGENTIC RESEARCH ---")
    print(f"Research question: {question}")

    result = run_agentic_research(
        question=question,
        index=index,
        chunks=chunks
    )

    # 7. Display planner output
    print("\n========== PLANNER OUTPUT ==========")

    for i, subquestion in enumerate(
        result["subquestions"], start=1
    ):
        print(f"{i}. {subquestion}")

    # 8. Display retrieved evidence
    print("\n========== RETRIEVED EVIDENCE ==========")

    for i, item in enumerate(
        result["reranked_results"], start=1
    ):
        chunk = item["chunk"]

        print(f"\nEvidence {i}")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Paper: {chunk['paper_title']}")
        print(f"Section: {chunk['section']}")
        print(f"Page: {chunk['page_number']}")
        print(f"Reranker score: {item['reranker_score']}")
        print(f"Text: {chunk['text'][:300]}...")

    print("\nAgentic research workflow completed!")


if __name__ == "__main__":
    main()
