
from pathlib import Path

from src.pdf_parser import extract_pdf_text
from src.chunker import chunk_pages
from src.bm25_search import create_bm25_index
from src.hybrid_retriever import hybrid_search
from src.reranker import rerank_results
from src.agents.structured_extractor import (
    extract_structured_findings
)


def main():

    project_root = Path(__file__).resolve().parents[1]

    pdf_path = (
        project_root / "data" / "uploaded_pdfs" / "sample 2.pdf"
    )

    print("\n--- PDF PARSING ---")

    pages = extract_pdf_text(str(pdf_path))

    chunks = chunk_pages(
        pages=pages,
        paper_id="PAPER01",
        paper_title="Sample Research Paper"
    )

    print(f"Extracted {len(chunks)} chunks.")

    print("\n--- BM25 INDEX ---")

    index = create_bm25_index(chunks)

    question = (
        "Explain the Transformer architecture, "
        "its attention mechanisms, and limitations."
    )

    print("\n--- HYBRID RETRIEVAL ---")

    results = hybrid_search(
        index=index,
        chunks=chunks,
        query=question,
        top_k=5
    )

    print(f"Retrieved {len(results)} chunks.")

    print("\n--- RERANKING ---")

    reranked = rerank_results(
        query=question,
        results=results,
        top_k=5
    )

    print(f"Selected {len(reranked)} chunks.")

    print("\n--- STRUCTURED RESEARCH EXTRACTION ---")

    findings = extract_structured_findings(
        question=question,
        evidence=reranked
    )

    for category in [
        "models",
        "datasets",
        "performance",
        "methodology",
        "limitations"
    ]:

        print(f"\n========== {category.upper()} ==========")

        category_findings = [
            item for item in findings
            if item["category"] == category
        ]

        if not category_findings:
            print("No supporting findings extracted.")
            continue

        for item in category_findings:

            print("\nFinding:", item["finding"])

            for source in item["sources"]:
                print(
                    f"Source: {source['paper_title']} | "
                    f"Section: {source['section']} | "
                    f"Page: {source['page_number']} | "
                    f"Chunk: {source['citation_id']}"
                )

    print("\nStructured extraction completed!")


if __name__ == "__main__":
    main()
