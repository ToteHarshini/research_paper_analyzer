
from src.bm25_search import search_bm25
from src.vector_store import search_chunks


def hybrid_search(index, chunks, query, top_k=5, rrf_k=60):
    """
    Combine BM25 and vector search using Reciprocal Rank Fusion.
    """

    if not chunks:
        return []

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    # Retrieve candidates from BM25
    bm25_results = search_bm25(
        index=index,
        chunks=chunks,
        query=query,
        top_k=top_k * 2
    )

    # Retrieve candidates from ChromaDB
    vector_results = search_chunks(
        query=query,
        n_results=top_k * 2
    )

    # Map chunk IDs to their original chunk dictionaries
    chunks_by_id = {
        chunk["chunk_id"]: chunk
        for chunk in chunks
    }

    # Store combined RRF scores
    fused_scores = {}

    # Store each chunk's individual ranks
    rankings = {}

    # Process BM25 rankings
    for rank, (chunk, bm25_score) in enumerate(bm25_results, start=1):

        chunk_id = chunk["chunk_id"]

        fused_scores[chunk_id] = fused_scores.get(chunk_id, 0) + (
            1 / (rrf_k + rank)
        )

        rankings.setdefault(chunk_id, {})
        rankings[chunk_id]["bm25_rank"] = rank
        rankings[chunk_id]["bm25_score"] = float(bm25_score)

    # Process vector search rankings
    vector_ids = vector_results["ids"][0]
    vector_distances = vector_results["distances"][0]

    for rank, (chunk_id, distance) in enumerate(
        zip(vector_ids, vector_distances),
        start=1
    ):

        fused_scores[chunk_id] = fused_scores.get(chunk_id, 0) + (
            1 / (rrf_k + rank)
        )

        rankings.setdefault(chunk_id, {})
        rankings[chunk_id]["vector_rank"] = rank
        rankings[chunk_id]["vector_distance"] = float(distance)

    # Sort chunks by combined RRF score
    ranked_ids = sorted(
        fused_scores,
        key=lambda chunk_id: fused_scores[chunk_id],
        reverse=True
    )

    # Build final results
    results = []

    for chunk_id in ranked_ids[:top_k]:

        chunk = chunks_by_id.get(chunk_id)

        if chunk is None:
            continue

        results.append({
            "chunk": chunk,
            "rrf_score": fused_scores[chunk_id],
            "rankings": rankings[chunk_id]
        })

    return results
