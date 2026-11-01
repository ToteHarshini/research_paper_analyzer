
from src.hybrid_retriever import hybrid_search


def research_subquestions(index, chunks, subquestions, top_k=5):
    """
    Researcher Agent:
    Searches the research-paper database for evidence
    related to each subquestion.
    """

    if not subquestions:
        return []

    retrieved_by_id = {}

    for question in subquestions:
        print(f"\nSearching for: {question}")

        results = hybrid_search(
            index=index,
            chunks=chunks,
            query=question,
            top_k=top_k
        )

        for result in results:
            chunk = result["chunk"]
            chunk_id = chunk["chunk_id"]

            if chunk_id not in retrieved_by_id:
                updated_result = result.copy()
                updated_result["matched_subquestions"] = [question]

                retrieved_by_id[chunk_id] = updated_result

            else:
                retrieved_by_id[chunk_id]["matched_subquestions"].append(
                    question
                )

    return list(retrieved_by_id.values())
