
from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Load the model only once.
_reranker = None


def get_reranker():
    global _reranker

    if _reranker is None:
        print("Loading cross-encoder model...")
        _reranker = CrossEncoder(MODEL_NAME)

    return _reranker


def rerank_results(query, results, top_k=5):
    """
    Reorder hybrid retrieval results using a cross-encoder.

    Each result is expected to contain:
    {
        "chunk": {
            "text": "...",
            ...
        },
        "rrf_score": ...,
        "rankings": {...}
    }
    """

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    if not results:
        return []

    reranker = get_reranker()

    # Create (question, passage) pairs.
    pairs = [
        (query, result["chunk"]["text"])
        for result in results
    ]

    # Calculate relevance scores.
    scores = reranker.predict(pairs)

    # Preserve the original metadata and add the new score.
    ranked_results = []

    for result, score in zip(results, scores):
        updated_result = result.copy()
        updated_result["reranker_score"] = float(score)
        ranked_results.append(updated_result)

    # Highest relevance score comes first.
    ranked_results.sort(
        key=lambda item: item["reranker_score"],
        reverse=True
    )

    return ranked_results[:top_k]
