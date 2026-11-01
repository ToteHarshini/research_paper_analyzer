
import json
from src.llm import generate_gemini_response


def generate_subquestions(question):
    """
    Planner Agent:
    Breaks a complex research question into smaller,
    independently searchable research questions.
    """

    if not question or not question.strip():
        raise ValueError("Research question cannot be empty.")

    prompt = f"""
You are an academic research planning agent.

Your task is to break the user's research question
into smaller questions for scientific literature retrieval.

Original research question:
{question}

Instructions:
1. Identify the main research objectives.
2. Generate 3 to 6 focused subquestions.
3. Cover relevant methods, datasets, experimental results,
   limitations, and research gaps where applicable.
4. Avoid duplicate questions.
5. Make every question independently searchable.
6. Do not answer the questions.
7. Return only valid JSON in this format:

{{
    "subquestions": [
        "First subquestion",
        "Second subquestion",
        "Third subquestion"
    ]
}}
"""

    response = generate_gemini_response(
        prompt=prompt,
        temperature=0.2,
        response_mime_type="application/json"
    )

    if not response.text:
        raise RuntimeError("Planner returned an empty response.")

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError("Planner returned invalid JSON.") from exc

    subquestions = data.get("subquestions")

    if not isinstance(subquestions, list):
        raise ValueError("Invalid planner response format.")

    subquestions = [
        item.strip()
        for item in subquestions
        if isinstance(item, str) and item.strip()
    ]

    if not subquestions:
        raise ValueError("Planner generated no valid subquestions.")

    return subquestions
