

import json
import re

from src.llm import generate_gemini_response


def normalize_and_validate_citations(raw_citations, reason, status, evidence_by_id):
    """
    Robustly extract, normalize, and validate citations:
    - Normalizes string citations, bracketed citations (e.g. ['[PAPER01_C0003]']),
      and prefixed forms (e.g. 'Source ID: PAPER01_C0003').
    - Every recovered ID is validated against evidence_by_id (the candidate evidence
      actually supplied to the verifier).
    - If status is 'supported' or 'partially_supported' and raw_citations is empty,
      inspects the reasoning text: if a valid evidence ID is referenced in an affirmative,
      supporting context, recovers it while ensuring it is not treated as supporting if
      explicitly cited as contradictory, refuted, or unsupported.
    - If status is 'insufficient_evidence', returns [] unless partial support is present.
    """
    candidate_ids = []

    if isinstance(raw_citations, list):
        for item in raw_citations:
            if isinstance(item, str):
                cleaned = item.strip("[]'\" ")
                if cleaned in evidence_by_id:
                    candidate_ids.append(cleaned)
                else:
                    matches = re.findall(r"\b[A-Za-z0-9_]+\b", item)
                    for m in matches:
                        if m in evidence_by_id:
                            candidate_ids.append(m)
    elif isinstance(raw_citations, str):
        cleaned = raw_citations.strip("[]'\" ")
        if cleaned in evidence_by_id:
            candidate_ids.append(cleaned)
        else:
            matches = re.findall(r"\b[A-Za-z0-9_]+\b", raw_citations)
            for m in matches:
                if m in evidence_by_id:
                    candidate_ids.append(m)

    valid_citations = [
        cid for cid in candidate_ids
        if cid in evidence_by_id
    ]

    deduped = []
    for cid in valid_citations:
        if cid not in deduped:
            deduped.append(cid)

    if deduped:
        return deduped

    # Fallback recovery for supported or partially_supported claims when citations is empty
    if status in {"supported", "partially_supported"} and reason:
        reason_str = str(reason)
        # Check all evidence_by_id keys to see if any are referenced in reasoning
        recovered = []
        for cid in evidence_by_id:
            if cid in reason_str and cid not in recovered:
                # Do not treat as supporting if explicitly negated or contradicted in reasoning
                negation_pattern = re.compile(
                    rf"(?:not\s+supported\s+by|refuted\s+by|contradicted\s+by|lacks\s+evidence\s+in|unsupported\s+by)\s+{re.escape(cid)}",
                    re.IGNORECASE
                )
                if not negation_pattern.search(reason_str):
                    recovered.append(cid)
        if recovered:
            return recovered

    return []


def extract_and_verify_claims(question, evidence, max_evidence=6):
    """
    Joint Claim Extraction and Verification Agent:
    Extracts 3 to 5 key empirical claims and verifies each against the retrieved evidence
    in a SINGLE unified LLM call.

    Preserves:
    - 3 to 5 factual claims directly answering the inquiry.
    - Verification status for each claim (supported, contradicted, partially_supported, insufficient_evidence).
    - Evidence-grounded 1-2 sentence reasoning.
    - Exact Source IDs, paper titles, sections, and page numbers.
    - Explicit unsupported/unverified status when evidence is insufficient.
    """

    if not question or not question.strip():
        raise ValueError("Research question cannot be empty.")

    if not evidence:
        return []

    candidate_evidence = evidence[:max_evidence] if max_evidence else evidence
    evidence_by_id = {}

    for result in candidate_evidence:
        chunk = result["chunk"]
        evidence_by_id[chunk["chunk_id"]] = chunk

    evidence_text = ""

    for chunk_id, chunk in evidence_by_id.items():
        evidence_text += f"""
Source ID: {chunk_id}
Paper: {chunk.get('paper_title', 'Unknown')}
Section: {chunk.get('section', 'General')}
Page: {chunk.get('page_number', 'N/A')}
Text: {chunk['text']}
"""

    prompt = f"""
You are a scientific claim extraction and verification agent.

Research question:
{question}

Available research evidence:
{evidence_text}

Task:
1. Extract 3 to 5 important factual claims from the evidence that directly address the research question.
2. For each extracted claim, verify whether the provided evidence supports it, contradicts it, or is insufficient.
3. Assign an exact verification status:
   - supported: The evidence directly substantiates the claim. Cite all supporting Source IDs.
   - contradicted: The evidence directly conflicts with or refutes the claim. Cite the refuting Source IDs.
   - partially_supported: The evidence supports parts of the claim or conditions it. You MUST cite the exact Source IDs for the parts of the claim substantiated by the evidence.
   - insufficient_evidence: The evidence is insufficient to verify the claim. Use an empty citation list [].
4. Provide a concise explanation (1 to 2 sentences) grounded strictly in the evidence.
5. Cite only the exact Source IDs provided above.
6. Do not introduce outside knowledge or unverified assumptions.

Return only valid JSON in this format:

{{
    "verifications": [
        {{
            "claim": "Claim text",
            "status": "supported",
            "reason": "Direct evidence explanation",
            "citations": ["PAPER01_C0001"]
        }}
    ]
}}
"""

    response = generate_gemini_response(
        prompt=prompt,
        temperature=0.1,
        max_output_tokens=1200,
        response_mime_type="application/json"
    )

    if not response.text:
        raise RuntimeError("Claim verification returned an empty response.")

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError("Claim verification returned invalid JSON.") from exc

    verifications = data.get("verifications")

    if not isinstance(verifications, list):
        raise ValueError("Invalid claim verification response format.")

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

        valid_citations = normalize_and_validate_citations(
            raw_citations=citations,
            reason=item.get("reason", ""),
            status=status,
            evidence_by_id=evidence_by_id
        )

        verified_results.append({
            "claim": item.get("claim", "").strip(),
            "status": status,
            "reason": item.get("reason", "").strip(),
            "citations": valid_citations
        })

    return verified_results


def verify_claims(question, claims, evidence, max_evidence=6):
    """
    Verifies research claims against retrieved evidence.
    Limits candidate evidence to the top reranked chunks to respect token budgets
    while preserving complete passages, citations, section metadata, and page numbers.
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

    candidate_evidence = evidence[:max_evidence] if max_evidence else evidence
    evidence_by_id = {}

    for result in candidate_evidence:
        chunk = result["chunk"]
        evidence_by_id[chunk["chunk_id"]] = chunk

    evidence_text = ""

    for chunk_id, chunk in evidence_by_id.items():
        evidence_text += f"""
Source ID: {chunk_id}
Paper: {chunk.get('paper_title', 'Unknown')}
Section: {chunk.get('section', 'General')}
Page: {chunk.get('page_number', 'N/A')}
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
6. Keep each verification reason concise (1 to 2 sentences directly citing the evidence).

Return only valid JSON:

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

    response = generate_gemini_response(
        prompt=prompt,
        temperature=0.1,
        max_output_tokens=1400,
        response_mime_type="application/json"
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

        valid_citations = normalize_and_validate_citations(
            raw_citations=citations,
            reason=item.get("reason", ""),
            status=status,
            evidence_by_id=evidence_by_id
        )

        verified_results.append({
            "claim": item.get("claim", ""),
            "status": status,
            "reason": item.get("reason", ""),
            "citations": valid_citations
        })

    return verified_results


def extract_claims(question, evidence, max_chunks=5):
    """
    Extracts factual claims from retrieved research evidence.
    Uses the top reranked chunks to minimize token overhead while
    preserving source context, section names, page numbers, and passage fidelity.
    """

    if not evidence:
        return []

    candidate_evidence = evidence[:max_chunks] if max_chunks else evidence
    evidence_text = ""

    for result in candidate_evidence:
        chunk = result["chunk"]

        evidence_text += f"""
Source ID: {chunk['chunk_id']}
Paper: {chunk.get('paper_title', 'Unknown')}
Section: {chunk.get('section', 'General')}
Page: {chunk.get('page_number', 'N/A')}
Text: {chunk['text']}
"""

    prompt = f"""
You are a scientific research claim extraction agent.

Research question:
{question}

Retrieved evidence:
{evidence_text}

Extract 3 to 5 important factual claims that help answer
the research question.

Rules:
1. Use only the supplied evidence.
2. Do not introduce outside knowledge.
3. Each claim must express one clear, concise factual statement (1 sentence).
4. Do not make unsupported assumptions.

Return only valid JSON:

{{
    "claims": [
        "First factual claim",
        "Second factual claim"
    ]
}}
"""

    response = generate_gemini_response(
        prompt=prompt,
        temperature=0.1,
        max_output_tokens=600,
        response_mime_type="application/json"
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
