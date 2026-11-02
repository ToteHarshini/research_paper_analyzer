import json
from unittest.mock import patch, MagicMock
import pytest

from src.pdf_parser import extract_pdf_text
from src.chunker import chunk_text, chunk_pages, detect_section, find_section_headings_with_offsets
from src.bm25_search import create_bm25_index, search_bm25
from src.reranker import rerank_results
from src.llm import LLMResponse
from src.agents.planner import generate_subquestions
from src.agents.researcher import research_subquestions
from src.agents.verifier import (
    verify_claims,
    extract_claims,
    extract_and_verify_claims,
    normalize_and_validate_citations
)
from src.agents.structured_extractor import extract_structured_findings
from src.agents.report_generator import generate_final_report, select_report_evidence
from src.research_workflow import run_agentic_research
from src.db.crud import hash_password, verify_password


# ---------------------------------------------------------------------------
# 1. PARSER & CHUNKER UNIT TESTS
# ---------------------------------------------------------------------------

def test_chunk_text_sliding_window():
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = chunk_text(text, chunk_size=10, overlap=3)
    assert len(chunks) > 1
    assert chunks[0] == "abcdefghij"
    assert chunks[1] == "hijklmnopq"  # 10 - 3 = 7 start offset


def test_detect_section():
    text = "1. Introduction\nIn this work, we propose a new model."
    section = detect_section(text, current_section="Unknown")
    assert section == "Introduction"

    text_no_heading = "Just regular paragraph without section."
    section_unchanged = detect_section(text_no_heading, current_section="Introduction")
    assert section_unchanged == "Introduction"


def test_chunk_pages_metadata():
    pages = [
        {"page": 1, "text": "Abstract\nThis paper introduces Transformer architecture."},
        {"page": 2, "text": "2. Background\nAttention mechanisms have become standard."}
    ]
    chunks = chunk_pages(
        pages=pages,
        paper_id="PAPER01",
        paper_title="Attention Paper",
        chunk_size=100,
        overlap=20
    )
    assert len(chunks) >= 2
    for chunk in chunks:
        assert "chunk_id" in chunk
        assert chunk["paper_id"] == "PAPER01"
        assert chunk["paper_title"] == "Attention Paper"
        assert chunk["page_number"] in [1, 2]
        assert chunk["section"] in ["Abstract", "Background"]
        assert len(chunk["text"]) > 0


def test_pdf_parser_on_sample_pdf():
    pdf_path = "data/uploaded_pdfs/sample 2.pdf"
    pages = extract_pdf_text(pdf_path)
    assert len(pages) == 15
    assert pages[0]["page"] == 1
    assert "Attention Is All You Need" in pages[0]["text"]


# ---------------------------------------------------------------------------
# 2. RETRIEVAL & RERANKER UNIT TESTS
# ---------------------------------------------------------------------------

def test_bm25_index_and_search():
    sample_chunks = [
        {"chunk_id": "C1", "text": "The transformer uses scaled dot-product attention."},
        {"chunk_id": "C2", "text": "Convolutional networks process spatial imagery."},
        {"chunk_id": "C3", "text": "Recurrent neural networks process sequential data with hidden states."}
    ]
    index = create_bm25_index(sample_chunks)
    results = search_bm25(index, sample_chunks, query="scaled attention", top_k=2)

    assert len(results) == 2
    top_chunk, top_score = results[0]
    assert top_chunk["chunk_id"] == "C1"
    assert top_score > 0


def test_reranker_offline():
    query = "What attention mechanism does Transformer use?"
    results = [
        {
            "chunk": {"chunk_id": "C1", "text": "Transformers rely solely on self-attention mechanisms."},
            "rrf_score": 0.03
        },
        {
            "chunk": {"chunk_id": "C2", "text": "Unrelated passage about computer graphics rendering."},
            "rrf_score": 0.02
        }
    ]
    reranked = rerank_results(query=query, results=results, top_k=2)
    assert len(reranked) == 2
    assert "reranker_score" in reranked[0]
    assert reranked[0]["chunk"]["chunk_id"] == "C1"
    assert reranked[0]["reranker_score"] >= reranked[1]["reranker_score"]


# ---------------------------------------------------------------------------
# 3. AGENT TESTS (USING MOCKED LLM RESPONSES)
# ---------------------------------------------------------------------------

@patch("src.agents.planner.generate_gemini_response")
def test_planner_agent_mocked(mock_llm):
    mock_llm.return_value = LLMResponse(json.dumps({
        "subquestions": [
            "What is self-attention?",
            "What datasets were evaluated?",
            "What are the computational limitations?"
        ]
    }))

    subquestions = generate_subquestions("Explain the Transformer architecture.")
    assert len(subquestions) == 3
    assert subquestions[0] == "What is self-attention?"
    assert mock_llm.called


@patch("src.agents.researcher.hybrid_search")
def test_researcher_agent(mock_hybrid):
    mock_hybrid.side_effect = [
        [{"chunk": {"chunk_id": "C1", "text": "Evidence 1"}}],
        [{"chunk": {"chunk_id": "C1", "text": "Evidence 1"}}, {"chunk": {"chunk_id": "C2", "text": "Evidence 2"}}]
    ]

    results = research_subquestions(
        index=MagicMock(),
        chunks=[],
        subquestions=["Subq 1", "Subq 2"],
        top_k=2
    )

    assert len(results) == 2
    c1 = next(r for r in results if r["chunk"]["chunk_id"] == "C1")
    assert "Subq 1" in c1["matched_subquestions"]
    assert "Subq 2" in c1["matched_subquestions"]


@patch("src.agents.verifier.generate_gemini_response")
def test_claim_extractor_and_verifier_mocked(mock_llm):
    # Mock extract_claims
    mock_llm.return_value = LLMResponse(json.dumps({
        "claims": ["Transformer does not use recurrence.", "Transformer achieves 28.4 BLEU."]
    }))

    evidence = [
        {"chunk": {"chunk_id": "C1", "paper_title": "Paper 1", "section": "Abstract", "page_number": 1, "text": "Transformer dispenses with recurrence."}}
    ]

    claims = extract_claims("What is Transformer?", evidence)
    assert len(claims) == 2
    assert claims[0] == "Transformer does not use recurrence."

    # Mock verify_claims
    mock_llm.return_value = LLMResponse(json.dumps({
        "verifications": [
            {
                "claim": "Transformer does not use recurrence.",
                "status": "supported",
                "reason": "Directly stated in Abstract.",
                "citations": ["C1"]
            }
        ]
    }))

    verified = verify_claims("What is Transformer?", claims[:1], evidence)
    assert len(verified) == 1
    assert verified[0]["status"] == "supported"
    assert verified[0]["citations"] == ["C1"]


@patch("src.agents.verifier.generate_gemini_response")
def test_extract_and_verify_claims_mocked(mock_llm):
    """
    Test joint claim extraction and verification in a single LLM invocation.
    Validates:
    - 3-5 factual claims with verification status
    - 1-2 sentence evidence-grounded reason
    - Exact Source IDs verified against candidate chunks
    - Unknown/hallucinated citations filtered out
    """
    mock_llm.return_value = LLMResponse(json.dumps({
        "verifications": [
            {
                "claim": "Transformer achieves 28.4 BLEU on English-to-German.",
                "status": "supported",
                "reason": "Directly substantiated by evaluation results in Table 2.",
                "citations": ["PAPER01_C0001", "NON_EXISTENT_CHUNK"]
            },
            {
                "claim": "Transformer utilizes recurrent hidden states.",
                "status": "contradicted",
                "reason": "The paper explicitly states the architecture dispenses with recurrence entirely.",
                "citations": ["PAPER01_C0001"]
            },
            {
                "claim": "Transformer models exhibit human-level speech synthesis.",
                "status": "insufficient_evidence",
                "reason": "Provided evidence only evaluates machine translation tasks.",
                "citations": []
            }
        ]
    }))

    evidence = [
        {
            "chunk": {
                "chunk_id": "PAPER01_C0001",
                "paper_title": "Attention Is All You Need",
                "section": "Abstract",
                "page_number": 1,
                "text": "The Transformer is the first transduction model relying entirely on self-attention."
            }
        }
    ]

    results = extract_and_verify_claims(
        question="What are the capabilities of the Transformer model?",
        evidence=evidence,
        max_evidence=5
    )

    assert len(results) == 3
    # Check claim 1
    assert results[0]["claim"] == "Transformer achieves 28.4 BLEU on English-to-German."
    assert results[0]["status"] == "supported"
    # NON_EXISTENT_CHUNK must be filtered out
    assert results[0]["citations"] == ["PAPER01_C0001"]
    assert "substantiated" in results[0]["reason"]

    # Check claim 2
    assert results[1]["status"] == "contradicted"
    assert results[1]["citations"] == ["PAPER01_C0001"]

    # Check claim 3
    assert results[2]["status"] == "insufficient_evidence"
    assert results[2]["citations"] == []


@patch("src.agents.structured_extractor.generate_gemini_response")
def test_structured_extractor_mocked(mock_llm):
    mock_llm.return_value = LLMResponse(json.dumps({
        "findings": [
            {
                "category": "models",
                "finding": "Transformer with Multi-Head Attention",
                "citation_ids": ["C1"]
            },
            {
                "category": "performance",
                "finding": "Achieves 28.4 BLEU on English-to-German",
                "citation_ids": ["C1"]
            }
        ]
    }))

    evidence = [
        {"chunk": {"chunk_id": "C1", "paper_id": "P1", "paper_title": "Paper 1", "section": "Results", "page_number": 1, "text": "Transformer achieves 28.4 BLEU."}}
    ]

    findings = extract_structured_findings("What models and performance were reported?", evidence, max_evidence=5)
    assert len(findings) == 2
    assert findings[0]["category"] == "models"
    assert findings[1]["category"] == "performance"
    assert len(findings[0]["sources"]) == 1
    assert findings[0]["sources"][0]["citation_id"] == "C1"


@patch("src.agents.report_generator.generate_gemini_response")
def test_report_generator_with_structured_findings_mocked(mock_llm):
    mock_llm.return_value = LLMResponse("# 1. Executive Summary\nTransformer is a neural architecture.")

    evidence = [
        {"chunk": {"chunk_id": "C1", "paper_id": "P1", "paper_title": "Paper 1", "section": "Abstract", "page_number": 1, "text": "Transformer details."}}
    ]
    verified_claims = [
        {"claim": "Transformer achieves 28.4 BLEU", "status": "supported", "reason": "stated in paper", "citations": ["C1"]}
    ]
    structured_findings = [
        {"category": "models", "finding": "Base Transformer", "sources": [{"citation_id": "C1"}]}
    ]

    report = generate_final_report(
        question="How does Transformer perform?",
        evidence=evidence,
        verified_claims=verified_claims,
        structured_findings=structured_findings
    )

    assert "Executive Summary" in report
    # Verify mock was called and prompt contained structured findings
    call_args = mock_llm.call_args[1]
    assert "Structured findings by category:" in call_args["prompt"]
    assert "Base Transformer" in call_args["prompt"]


# ---------------------------------------------------------------------------
# 4. FULL LANGGRAPH AGENT WORKFLOW END-TO-END (MOCKED LLM)
# ---------------------------------------------------------------------------

@patch("src.agents.report_generator.generate_gemini_response")
@patch("src.agents.structured_extractor.generate_gemini_response")
@patch("src.agents.verifier.generate_gemini_response")
@patch("src.agents.planner.generate_gemini_response")
def test_run_agentic_research_graph_end_to_end_mocked(
    mock_planner,
    mock_verifier,
    mock_structured,
    mock_report
):
    # Mock Planner
    mock_planner.return_value = LLMResponse(json.dumps({
        "subquestions": ["How does attention work?"]
    }))

    # Mock Verifier (single unified call for claim extraction and verification)
    mock_verifier.return_value = LLMResponse(json.dumps({
        "verifications": [
            {
                "claim": "Attention connects encoder and decoder.",
                "status": "supported",
                "reason": "Explicitly stated in paper.",
                "citations": ["PAPER01_C0001"]
            }
        ]
    }))

    # Mock Structured Extractor
    mock_structured.return_value = LLMResponse(json.dumps({
        "findings": [
            {
                "category": "methodology",
                "finding": "Multi-Head Attention",
                "citation_ids": ["PAPER01_C0001"]
            }
        ]
    }))

    # Mock Report Generator
    mock_report.return_value = LLMResponse("# 1. Executive Summary\nComplete synthesized report.")

    chunks = [
        {
            "chunk_id": "PAPER01_C0001",
            "paper_id": "PAPER01",
            "paper_title": "Sample Paper",
            "section": "Abstract",
            "page_number": 1,
            "text": "The Transformer uses attention mechanisms without recurrence."
        }
    ]
    index = create_bm25_index(chunks)

    result = run_agentic_research(
        question="Explain the Transformer architecture.",
        index=index,
        chunks=chunks
    )

    # Validate full state flow
    assert "subquestions" in result
    assert result["subquestions"] == ["How does attention work?"]
    assert "retrieved_results" in result
    assert "reranked_results" in result
    assert "claims" in result
    assert "verified_claims" in result
    assert "structured_findings" in result
    assert len(result["structured_findings"]) == 1
    assert "final_report" in result
    assert "Complete synthesized report" in result["final_report"]


# ---------------------------------------------------------------------------
# 5. PASSWORD HASHING AND AUTH CRUDS
# ---------------------------------------------------------------------------

def test_password_hashing():
    raw_password = "SuperSecretPassword123!"
    hashed = hash_password(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


# ---------------------------------------------------------------------------
# 6. TARGETED FIXES REGRESSION TESTS
# ---------------------------------------------------------------------------

def test_headings_split_across_lines():
    """
    Test section detection handles split-line headings:
    - Number on line N, heading title on line N+1 (e.g. '7\\nConclusion', '1.\\nIntroduction')
    - Multi-word heading split across lines (e.g. 'Related\\nWork')
    """
    text1 = "Some introductory text.\n7\nConclusion\nThis is the concluding paragraph."
    headings1 = find_section_headings_with_offsets(text1)
    assert len(headings1) == 1
    assert headings1[0][1] == "Conclusion"

    text2 = "Prior discussion.\n1.\nIntroduction\nWe introduce our novel approach."
    headings2 = find_section_headings_with_offsets(text2)
    assert len(headings2) == 1
    assert headings2[0][1] == "Introduction"

    text3 = "Previous work.\nRelated\nWork\nHere we review prior literature."
    headings3 = find_section_headings_with_offsets(text3)
    assert len(headings3) == 1
    assert headings3[0][1] == "Related Work"


def test_offset_aware_section_detection_multi_headings_per_page():
    """
    Test that chunks on a single page with multiple headings are assigned
    their respective sections based on character offsets rather than taking
    the final heading for the whole page.
    """
    # 300 chars of Results, then Conclusion heading, then 400 chars of Conclusion,
    # then References heading, then References content.
    p_text = (
        "Evaluation Results on Test Set.\n" + ("The model achieves high accuracy. " * 10) + "\n\n"
        "Conclusion\n" + ("In this work, we presented the unified architecture. " * 12) + "\n\n"
        "References\n" + ("[1] Author et al. Title. 2020.\n" * 10)
    )

    pages = [{"page": 1, "text": p_text}]
    chunks = chunk_pages(
        pages=pages,
        paper_id="TEST01",
        paper_title="Multi Heading Paper",
        chunk_size=350,
        overlap=50
    )

    sections_found = [c["section"] for c in chunks]
    # The beginning must be Unknown or Results, middle Conclusion, and tail References
    assert "Conclusion" in sections_found
    assert "References" in sections_found
    assert sections_found[0] != "References"  # Must NOT be overwritten by References!
    assert sections_found[-1] == "References"


def test_sample_paper_c0040_to_c0043_section_labels():
    """
    Verify on sample 2.pdf that:
    - PAPER01_C0040 is Results
    - PAPER01_C0041 is Conclusion
    - PAPER01_C0042 is Conclusion
    - PAPER01_C0043 is References
    """
    pages = extract_pdf_text("data/uploaded_pdfs/sample 2.pdf")
    chunks = chunk_pages(pages, "PAPER01", "Attention Is All You Need")

    expected_labels = {
        "PAPER01_C0040": "Results",
        "PAPER01_C0041": "Conclusion",
        "PAPER01_C0042": "Conclusion",
        "PAPER01_C0043": "References"
    }

    for cid, exp_sec in expected_labels.items():
        chunk = next((c for c in chunks if c["chunk_id"] == cid), None)
        assert chunk is not None, f"Chunk {cid} not found in chunked output."
        assert chunk["section"] == exp_sec, f"{cid} expected {exp_sec}, got {chunk['section']}"


def test_select_report_evidence_promotes_results_passage():
    """
    Test select_report_evidence ensures relevant experimental/results passages
    are included in the report evidence even if ranked below architectural chunks,
    while fully preserving Source IDs, paper titles, sections, page numbers, and passage text.
    """
    evidence = [
        {"chunk": {"chunk_id": "C01", "paper_id": "P1", "paper_title": "Paper 1", "section": "Background", "page_number": 2, "text": "Passage 1"}},
        {"chunk": {"chunk_id": "C02", "paper_id": "P1", "paper_title": "Paper 1", "section": "Background", "page_number": 2, "text": "Passage 2"}},
        {"chunk": {"chunk_id": "C03", "paper_id": "P1", "paper_title": "Paper 1", "section": "Methodology", "page_number": 3, "text": "Passage 3"}},
        {"chunk": {"chunk_id": "C04", "paper_id": "P1", "paper_title": "Paper 1", "section": "Methodology", "page_number": 4, "text": "Passage 4"}},
        {"chunk": {"chunk_id": "C05", "paper_id": "P1", "paper_title": "Paper 1", "section": "Results", "page_number": 8, "text": "Table 2 summarizes BLEU scores of 28.4."}},
        {"chunk": {"chunk_id": "C06", "paper_id": "P1", "paper_title": "Paper 1", "section": "Results", "page_number": 9, "text": "Ablation results on head count."}}
    ]

    selected = select_report_evidence(evidence, question="What are the experimental results?", max_evidence=5)
    selected_ids = [r["chunk"]["chunk_id"] for r in selected]

    # Results chunk must be included in the candidate evidence
    assert "C05" in selected_ids
    # All metadata preserved
    c05 = next(r["chunk"] for r in selected if r["chunk"]["chunk_id"] == "C05")
    assert c05["paper_id"] == "P1"
    assert c05["paper_title"] == "Paper 1"
    assert c05["section"] == "Results"
    assert c05["page_number"] == 8
    assert "Table 2 summarizes BLEU scores of 28.4." in c05["text"]


def test_citation_normalization_and_recovery():
    """
    Test robust normalization and recovery of citations:
    - Normalizes bracketed IDs and prefixed forms.
    - Normalizes string-valued citations.
    - Recovers citations from reasoning text for partially supported claims.
    - Rejects IDs with explicit negation/contradiction in reasoning.
    - Filters out unsupplied/hallucinated IDs.
    """
    evidence_by_id = {
        "PAPER01_C0001": {"chunk_id": "PAPER01_C0001"},
        "PAPER01_C0003": {"chunk_id": "PAPER01_C0003"}
    }

    # 1. Bracketed list
    c1 = normalize_and_validate_citations(
        raw_citations=["[PAPER01_C0003]"],
        reason="Supported by paper.",
        status="supported",
        evidence_by_id=evidence_by_id
    )
    assert c1 == ["PAPER01_C0003"]

    # 2. String-valued citation
    c2 = normalize_and_validate_citations(
        raw_citations="PAPER01_C0003",
        reason="Supported by paper.",
        status="supported",
        evidence_by_id=evidence_by_id
    )
    assert c2 == ["PAPER01_C0003"]

    # 3. Prefixed citation string in list
    c3 = normalize_and_validate_citations(
        raw_citations=["Source ID: PAPER01_C0003 (Page 1)"],
        reason="Supported by paper.",
        status="supported",
        evidence_by_id=evidence_by_id
    )
    assert c3 == ["PAPER01_C0003"]

    # 4. Partially supported claim with empty raw_citations, but supported reference in reasoning
    c4 = normalize_and_validate_citations(
        raw_citations=[],
        reason="PAPER01_C0003 confirms that attention replaces RNNs, but does not benchmark parsing accuracy.",
        status="partially_supported",
        evidence_by_id=evidence_by_id
    )
    assert c4 == ["PAPER01_C0003"]

    # 5. Mention in reasoning with explicit negation must NOT be treated as supporting
    c5 = normalize_and_validate_citations(
        raw_citations=[],
        reason="This claim is not supported by PAPER01_C0003.",
        status="partially_supported",
        evidence_by_id=evidence_by_id
    )
    assert c5 == []

    # 6. Insufficient evidence status must not recover citations
    c6 = normalize_and_validate_citations(
        raw_citations=[],
        reason="No evidence in PAPER01_C0003.",
        status="insufficient_evidence",
        evidence_by_id=evidence_by_id
    )
    assert c6 == []

    # 7. Unsupplied/unknown ID filtered out
    c7 = normalize_and_validate_citations(
        raw_citations=["PAPER99_C9999"],
        reason="Supported by text.",
        status="supported",
        evidence_by_id=evidence_by_id
    )
    assert c7 == []


@patch("src.agents.structured_extractor.generate_gemini_response")
def test_structured_extractor_differentiates_author_limitations_and_research_gaps(mock_llm):
    """
    Test that structured extractor separates author-stated limitations from system-inferred research gaps.
    """
    mock_llm.return_value = LLMResponse(json.dumps({
        "findings": [
            {
                "category": "author_limitations",
                "finding": "The authors explicitly note that self-attention has quadratic complexity O(n^2) with sequence length.",
                "citation_ids": ["PAPER01_C0001"]
            },
            {
                "category": "research_gaps",
                "finding": "Cross-domain generalization to low-resource speech translation remains uninvestigated.",
                "citation_ids": ["PAPER01_C0001"]
            }
        ]
    }))

    evidence = [
        {"chunk": {"chunk_id": "PAPER01_C0001", "paper_id": "P1", "paper_title": "Title", "section": "Complexity", "page_number": 5, "text": "Complexity text"}}
    ]

    findings = extract_structured_findings("What are limitations and gaps?", evidence)
    assert len(findings) == 2
    assert findings[0]["category"] == "author_limitations"
    assert "quadratic complexity" in findings[0]["finding"]
    assert findings[1]["category"] == "research_gaps"
    assert "low-resource speech" in findings[1]["finding"]


@patch("src.agents.report_generator.generate_gemini_response")
def test_report_generator_prompt_distinguishes_limitations_and_gaps(mock_llm):
    """
    Test that generate_final_report prompt includes distinct sections for
    Research Gaps and Limitations, with dedicated subsections for Author-Stated Limitations
    and System-Inferred Limitations.
    """
    mock_llm.return_value = LLMResponse("# 1. Executive Summary\nReport output.")

    evidence = [
        {"chunk": {"chunk_id": "C1", "paper_id": "P1", "paper_title": "Paper", "section": "Results", "page_number": 8, "text": "Results text."}}
    ]
    verified_claims = [
        {"claim": "Transformer achieves 28.4 BLEU", "status": "supported", "reason": "stated in paper", "citations": ["C1"]}
    ]
    structured_findings = [
        {"category": "author_limitations", "finding": "Quadratic attention memory.", "sources": [{"citation_id": "C1"}]},
        {"category": "research_gaps", "finding": "Multimodal speech unexplored.", "sources": [{"citation_id": "C1"}]}
    ]

    report = generate_final_report(
        question="How does Transformer perform?",
        evidence=evidence,
        verified_claims=verified_claims,
        structured_findings=structured_findings
    )

    assert "Executive Summary" in report
    call_prompt = mock_llm.call_args[1]["prompt"]

    # Verify structured findings distinguish categories
    assert "[Author-Stated Limitation]" in call_prompt
    assert "[Research Gap]" in call_prompt

    # Verify report prompt requests distinct sections and subsections
    assert "# 6. Research Gaps" in call_prompt
    assert "# 7. Limitations and Uncertainty" in call_prompt
    assert "### Author-Stated Limitations" in call_prompt
    assert "### System-Inferred Limitations & Analytical Uncertainties" in call_prompt
    assert "# 4. Comparison of Methods and Results" in call_prompt
