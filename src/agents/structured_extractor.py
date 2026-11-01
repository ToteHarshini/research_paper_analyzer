
import json

from src.llm import generate_gemini_response


ALLOWED_CATEGORIES = {
    "models",
    "datasets",
    "performance",
    "methodology",
    "limitations"
}


def extract_structured_findings(question, evidence):
    """
    Extract structured research findings from retrieved evidence.

    Each finding is linked to the original paper chunks
    so that its source can be traced.
    """

    if not evidence:
        return []

    # Prepare evidence for Gemini
    evidence_text = []

    for result in evidence[:5]:
        chunk = result["chunk"]

        evidence_text.append({
            "citation_id": chunk["chunk_id"],
            "paper_id": chunk.get("paper_id", "Unknown"),
            "paper_title": chunk.get("paper_title", "Unknown"),
            "section": chunk.get("section", "Unknown"),
            "page_number": chunk.get("page_number", "Unknown"),
            "text": chunk["text"][:700]
        })

    prompt = f"""
You are a scientific research information extraction agent.

Research question:
{question}

Your task is to extract important research findings from the
provided evidence.

Organize findings into these categories:

1. models
2. datasets
3. performance
4. methodology
5. limitations

Evidence:
{json.dumps(evidence_text, indent=2)}

Return ONLY valid JSON in this format:

{{
    "findings": [
        {{
            "category": "models",
            "finding": "The study uses a Transformer architecture.",
            "citation_ids": ["PAPER01_C0001"]
        }}
    ]
}}

Important rules:

- Extract only information explicitly supported by the evidence.
- Do not invent model names, dataset names, metrics or results.
- Preserve numerical values and their units exactly.
- Do not assume that a result applies to datasets or experiments
  not mentioned in the evidence.
- Every finding must have at least one valid citation ID.
- Use only citation IDs provided in the evidence.
- If a category has no supporting evidence, return no finding
  for that category.
- Keep findings concise and scientifically accurate.
"""

    response = generate_gemini_response(
        prompt=prompt,
        temperature=0.1,
        max_output_tokens=2000,
        response_mime_type="application/json"
    )

    data = json.loads(response.text)

    valid_citation_ids = {
        item["citation_id"]: item for item in evidence_text
    }

    structured_findings = []

    for finding in data.get("findings", []):

        category = finding.get("category", "").lower()
        description = finding.get("finding", "").strip()
        citation_ids = finding.get("citation_ids", [])

        if category not in ALLOWED_CATEGORIES:
            continue

        if not description or not isinstance(citation_ids, list):
            continue

        # Keep only citations that actually exist
        valid_sources = [
            valid_citation_ids[citation_id]
            for citation_id in citation_ids
            if citation_id in valid_citation_ids
        ]

        if not valid_sources:
            continue

        structured_findings.append({
            "category": category,
            "finding": description,
            "sources": valid_sources
        })

    return structured_findings
