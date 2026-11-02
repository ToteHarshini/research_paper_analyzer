
import json
import re

from src.llm import generate_gemini_response


ALLOWED_CATEGORIES = {
    "models",
    "datasets",
    "performance",
    "methodology",
    "author_limitations",
    "research_gaps",
    "limitations"
}


def extract_structured_findings(question, evidence, max_evidence=6):
    """
    Extract structured research findings from retrieved evidence.

    Each finding is linked to the original paper chunks
    so that its source can be traced.

    Args:
        question: Research question.
        evidence: List of reranked retrieved chunks.
        max_evidence: Maximum candidate chunks to process. Defaults to 6
                      to provide comprehensive multi-section coverage
                      while strictly respecting provider rate limits.
    """

    if not evidence:
        return []

    # Prepare evidence for LLM (bounded by max_evidence)
    evidence_text = []

    for result in evidence[:max_evidence]:
        chunk = result["chunk"]

        evidence_text.append({
            "citation_id": chunk["chunk_id"],
            "paper_id": chunk.get("paper_id", "Unknown"),
            "paper_title": chunk.get("paper_title", "Unknown"),
            "section": chunk.get("section", "Unknown"),
            "page_number": chunk.get("page_number", "Unknown"),
            "text": chunk["text"]
        })

    prompt = f"""
You are a scientific research information extraction agent.

Research question:
{question}

Your task is to extract important research findings from the
provided evidence.

Organize findings into these categories:

1. models: Model architectures, components, or parameter configurations.
2. datasets: Datasets, corpora, languages, or benchmarks evaluated.
3. performance: Quantitative evaluation metrics, scores (e.g. BLEU, F1), training costs, or speedups.
4. methodology: Training regimes, objectives, attention formulations, or algorithms.
5. author_limitations: Constraints, bounds, computational complexity, or weaknesses EXPLICITLY stated or admitted by the paper authors in the text (e.g., sequential generation bottleneck, memory footprint).
6. research_gaps: Open questions, unaddressed domains, missing baselines, or future research directions inferred from the evidence.

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
- Never attribute an inferred research gap as an explicit statement by the authors. Author limitations must be directly grounded in explicit statements in the text.
- Do not invent model names, dataset names, metrics or results.
- Preserve numerical values and their units exactly.
- Do not assume that a result applies to datasets or experiments not mentioned in the evidence.
- Every finding must have at least one valid citation ID.
- Use only citation IDs provided in the evidence.
- If a category has no supporting evidence, return no finding for that category.
- Extract 1 to 2 key findings per category where supported by evidence.
- Keep each finding concise and scientifically accurate (1 to 2 sentences each).
"""

    response = generate_gemini_response(
        prompt=prompt,
        temperature=0.1,
        max_output_tokens=1200,
        response_mime_type="application/json"
    )

    if not response.text:
        return []

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError("Structured extractor returned invalid JSON.") from exc

    valid_citation_ids = {
        item["citation_id"]: item for item in evidence_text
    }

    structured_findings = []

    for finding in data.get("findings", []):

        category = finding.get("category", "").lower()
        description = finding.get("finding", "").strip()
        raw_citation_ids = finding.get("citation_ids", [])

        if category not in ALLOWED_CATEGORIES:
            continue

        # Normalize legacy 'limitations' to 'author_limitations'
        if category == "limitations":
            category = "author_limitations"

        if not description:
            continue

        # Normalize citation IDs robustly
        candidate_ids = []
        if isinstance(raw_citation_ids, list):
            for item in raw_citation_ids:
                if isinstance(item, str):
                    cleaned = item.strip("[]'\" ")
                    if cleaned in valid_citation_ids:
                        candidate_ids.append(cleaned)
                    else:
                        matches = re.findall(r"\b[A-Za-z0-9_]+\b", item)
                        for m in matches:
                            if m in valid_citation_ids:
                                candidate_ids.append(m)
        elif isinstance(raw_citation_ids, str):
            cleaned = raw_citation_ids.strip("[]'\" ")
            if cleaned in valid_citation_ids:
                candidate_ids.append(cleaned)
            else:
                matches = re.findall(r"\b[A-Za-z0-9_]+\b", raw_citation_ids)
                for m in matches:
                    if m in valid_citation_ids:
                        candidate_ids.append(m)

        # Keep only citations that actually exist
        valid_sources = []
        seen_ids = set()
        for citation_id in candidate_ids:
            if citation_id in valid_citation_ids and citation_id not in seen_ids:
                valid_sources.append(valid_citation_ids[citation_id])
                seen_ids.add(citation_id)

        if not valid_sources:
            continue

        structured_findings.append({
            "category": category,
            "finding": description,
            "sources": valid_sources
        })

    return structured_findings
