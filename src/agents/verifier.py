
import json

from src.llm import client, MODEL_NAME
from google.genai import types

def verify_claims(question, claims, evidence):
    """
    Verifies research claims against retrieved evidence.
    """

    if not question or not question.strip():
        raise ValueError("Research question cannot be empty.")

    if not claims:
        return []

    if not evidence:
        return [
            {
                "claim": claim,
                "status": "insufficient_evidence",
                "reason": "No supporting evidence was retrieved.",
                "citations": []
            }
            for claim in claims
        ]

    evidence_by_id = {}

    for result in evidence:
        chunk = result["chunk"]
        evidence_by_id[chunk["chunk_id"]] = chunk

    evidence_text = ""

    for chunk_id, chunk in evidence_by_id.items():
        evidence_text += f"""
Source ID: {chunk_id}
Paper: {chunk['paper_title']}
Section: {chunk['section']}
Page: {chunk['page_number']}
Text: {chunk['text']}

"""

    prompt = f"""
You are a scientific claim verification agent.

Research question:
{question}

Claims to verify:
{json.dumps(claims, ensure_ascii=False)}

Available evidence:
{evidence_text}

For every claim:
1. Determine whether the evidence supports it.
2. Identify contradictory evidence.
3. Do not use outside knowledge.
4. Cite only source IDs supplied above.
5. If evidence is insufficient, say so.

Return only valid JSON in this format:

{{
    "verifications": [
        {{
            "claim": "Claim text",
            "status": "supported",
            "reason": "Explanation based on evidence",
            "citations": ["PAPER01_C0001"]
        }}
    ]
}}

Allowed statuses:
- supported
- contradicted
- partially_supported
- insufficient_evidence
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json"
        )
    )

    if not response.text:
        raise RuntimeError("Verifier returned an empty response.")

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError("Verifier returned invalid JSON.") from exc

    verifications = data.get("verifications")

    if not isinstance(verifications, list):
        raise ValueError("Invalid verifier response format.")

    valid_statuses = {
        "supported",
        "contradicted",
        "partially_supported",
        "insufficient_evidence"
    }

    verified_results = []

    for item in verifications:
        if not isinstance(item, dict):
            continue

        status = item.get("status")
        citations = item.get("citations", [])

        if status not in valid_statuses:
            status = "insufficient_evidence"

        if not isinstance(citations, list):
            citations = []

        # Reject citation IDs that are not in retrieved evidence.
        valid_citations = [
            citation
            for citation in citations
            if isinstance(citation, str)
            and citation in evidence_by_id
        ]

        verified_results.append({
            "claim": item.get("claim", ""),
            "status": status,
            "reason": item.get("reason", ""),
            "citations": valid_citations
        })

    return verified_results

def extract_claims(question, evidence):
    """
    Extracts factual claims from retrieved research evidence.
    These claims will be passed to verify_claims().
    """

    if not evidence:
        return []

    evidence_text = ""

    for result in evidence:
        chunk = result["chunk"]

        evidence_text += f"""
Source ID: {chunk['chunk_id']}
Paper: {chunk['paper_title']}
Page: {chunk['page_number']}
Text: {chunk['text']}

"""

    prompt = f"""
You are a scientific research claim extraction agent.

Research question:
{question}

Retrieved evidence:
{evidence_text}

Extract 3 to 8 important factual claims that help answer
the research question.

Rules:
1. Use only the supplied evidence.
2. Do not introduce outside knowledge.
3. Each claim must express one clear factual statement.
4. Do not make unsupported assumptions.

Return only valid JSON:

{{
    "claims": [
        "First factual claim",
        "Second factual claim"
    ]
}}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json"
        )
    )

    if not response.text:
        raise RuntimeError("Claim extraction returned an empty response.")

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid claim extraction JSON.") from exc

    claims = data.get("claims", [])

    if not isinstance(claims, list):
        raise ValueError("Invalid claims format.")

    return [
        claim.strip()
        for claim in claims
        if isinstance(claim, str) and claim.strip()
    ]
