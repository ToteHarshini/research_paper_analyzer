
from rank_bm25 import BM25Okapi


def create_bm25_index(chunks):
    """
    Create a BM25 index from research paper chunks.
    """

    if not chunks:
        raise ValueError("Cannot create BM25 index: no chunks provided.")

    tokenized = [
        chunk["text"].lower().split()
        for chunk in chunks
    ]

    return BM25Okapi(tokenized)


def search_bm25(index, chunks, query, top_k=5):
    """
    Search for relevant chunks using BM25 keyword matching.
    """

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    tokens = query.lower().split()

    scores = index.get_scores(tokens)

    ranked = sorted(
        zip(chunks, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return ranked[:top_k]
