import io
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app import app
from src.llm import LLMResponse


@pytest.fixture(name="client")
def fixture_client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. HEALTH ENDPOINT TEST
# ---------------------------------------------------------------------------

def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


# ---------------------------------------------------------------------------
# 2. VALIDATION & ERROR HANDLING TESTS FOR /api/analyze
# ---------------------------------------------------------------------------

def test_analyze_missing_question(client):
    """Verify that an empty or missing research question is rejected with 400."""
    pdf_content = b"%PDF-1.4 minimal pdf binary"
    files = [("files", ("test.pdf", io.BytesIO(pdf_content), "application/pdf"))]

    # Empty question
    response = client.post("/api/analyze", data={"question": "   "}, files=files)
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_analyze_invalid_file_extension(client):
    """Verify that non-PDF files are rejected with 400."""
    txt_content = b"Some plain text"
    files = [("files", ("paper.txt", io.BytesIO(txt_content), "text/plain"))]

    response = client.post("/api/analyze", data={"question": "Explain paper"}, files=files)
    assert response.status_code == 400
    assert "not a PDF" in response.json()["detail"]


def test_analyze_empty_file(client):
    """Verify that zero-byte files are rejected with 400."""
    files = [("files", ("empty.pdf", io.BytesIO(b""), "application/pdf"))]

    response = client.post("/api/analyze", data={"question": "Explain paper"}, files=files)
    assert response.status_code == 400
    assert "is empty" in response.json()["detail"]


def test_analyze_invalid_pdf_header(client):
    """Verify that files lacking the %PDF- header are rejected with 400."""
    fake_pdf = b"This is not a real PDF file"
    files = [("files", ("fake.pdf", io.BytesIO(fake_pdf), "application/pdf"))]

    response = client.post("/api/analyze", data={"question": "Explain paper"}, files=files)
    assert response.status_code == 400
    assert "missing PDF header" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 3. SUCCESSFUL ANALYSIS WITH SINGLE AND MULTIPLE PDFS
# ---------------------------------------------------------------------------

@patch("app.run_agentic_research")
@patch("app.store_chunks")
@patch("app.extract_pdf_text")
def test_analyze_single_valid_pdf(mock_extract, mock_store, mock_workflow, client):
    """Verify end-to-end flow of /api/analyze with a single valid PDF."""
    mock_extract.return_value = [
        {"page": 1, "text": "Abstract\nTransformers rely solely on attention mechanisms."}
    ]

    mock_workflow.return_value = {
        "question": "How do Transformers work?",
        "subquestions": ["What is self-attention?"],
        "final_report": "# 1. Executive Summary\nTransformers use attention.",
        "verified_claims": [
            {
                "claim": "Transformers use self-attention",
                "status": "supported",
                "reason": "Directly stated in Abstract",
                "citations": ["PAPER01_C0001"]
            }
        ],
        "structured_findings": [
            {
                "category": "models",
                "finding": "Transformer architecture",
                "sources": [{"citation_id": "PAPER01_C0001"}]
            }
        ],
        "reranked_results": [
            {
                "chunk": {
                    "chunk_id": "PAPER01_C0001",
                    "paper_id": "PAPER01",
                    "paper_title": "Attention Paper",
                    "section": "Abstract",
                    "page_number": 1,
                    "text": "Transformers rely solely on attention mechanisms."
                },
                "reranker_score": 7.5
            }
        ]
    }

    pdf_content = b"%PDF-1.4 sample valid content"
    files = [("files", ("attention_paper.pdf", io.BytesIO(pdf_content), "application/pdf"))]

    response = client.post(
        "/api/analyze",
        data={"question": "How do Transformers work?"},
        files=files
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "How do Transformers work?"
    assert len(data["subquestions"]) == 1
    assert "Executive Summary" in data["final_report"]
    assert len(data["verified_claims"]) == 1
    assert data["verified_claims"][0]["status"] == "supported"
    assert len(data["structured_findings"]) == 1
    assert data["structured_findings"][0]["category"] == "models"
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["chunk_id"] == "PAPER01_C0001"


@patch("app.run_agentic_research")
@patch("app.store_chunks")
@patch("app.extract_pdf_text")
def test_analyze_multiple_valid_pdfs(mock_extract, mock_store, mock_workflow, client):
    """Verify /api/analyze correctly processes multiple uploaded PDFs."""
    mock_extract.side_effect = [
        [{"page": 1, "text": "Paper 1 content regarding Transformer models."}],
        [{"page": 1, "text": "Paper 2 content regarding BERT and attention."}]
    ]

    mock_workflow.return_value = {
        "question": "Compare models in both papers.",
        "subquestions": ["What is Paper 1?", "What is Paper 2?"],
        "final_report": "Comparison report between Paper 1 and Paper 2.",
        "verified_claims": [],
        "structured_findings": [],
        "reranked_results": []
    }

    files = [
        ("files", ("paper1.pdf", io.BytesIO(b"%PDF-1.4 Paper 1 bytes"), "application/pdf")),
        ("files", ("paper2.pdf", io.BytesIO(b"%PDF-1.4 Paper 2 bytes"), "application/pdf"))
    ]

    response = client.post(
        "/api/analyze",
        data={"question": "Compare models in both papers."},
        files=files
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["subquestions"]) == 2
    assert "Comparison report" in data["final_report"]
    assert mock_extract.call_count == 2


# ---------------------------------------------------------------------------
# 4. FAILURE AND EXCEPTION HANDLING IN /api/analyze
# ---------------------------------------------------------------------------

@patch("app.store_chunks")
@patch("app.extract_pdf_text")
def test_analyze_malformed_pdf_handling(mock_extract, mock_store, client):
    """Verify that unparseable PDFs return 422 with a clean error message."""
    mock_extract.side_effect = RuntimeError("Corrupted PDF stream cannot be read")

    files = [("files", ("corrupt.pdf", io.BytesIO(b"%PDF-1.4 corrupt data"), "application/pdf"))]

    response = client.post(
        "/api/analyze",
        data={"question": "Analyze this corrupted PDF."},
        files=files
    )

    assert response.status_code == 422
    assert "Failed to parse PDF" in response.json()["detail"]


@patch("app.run_agentic_research")
@patch("app.store_chunks")
@patch("app.extract_pdf_text")
def test_analyze_missing_llm_key_handling(mock_extract, mock_store, mock_workflow, client):
    """Verify that missing LLM keys produce HTTP 503 instead of an unhandled crash."""
    mock_extract.return_value = [{"page": 1, "text": "Valid paper text."}]
    mock_workflow.side_effect = ValueError("No LLM API key found in .env file.")

    files = [("files", ("sample.pdf", io.BytesIO(b"%PDF-1.4 valid"), "application/pdf"))]

    response = client.post(
        "/api/analyze",
        data={"question": "What is the key contribution?"},
        files=files
    )

    assert response.status_code == 503
    assert "No LLM provider configured" in response.json()["detail"]


@patch("app.run_agentic_research")
@patch("app.store_chunks")
@patch("app.extract_pdf_text")
def test_analyze_connection_error_handling(mock_extract, mock_store, mock_workflow, client):
    """Verify that external LLM network connection errors produce HTTP 502."""
    mock_extract.return_value = [{"page": 1, "text": "Valid paper text."}]
    mock_workflow.side_effect = Exception("Connection error contacting Groq API")

    files = [("files", ("sample.pdf", io.BytesIO(b"%PDF-1.4 valid"), "application/pdf"))]

    response = client.post(
        "/api/analyze",
        data={"question": "What is the key contribution?"},
        files=files
    )

    assert response.status_code == 502
    assert "Failed to connect to the external LLM service" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 5. FOLLOW-UP CHAT ENDPOINT TESTS (/api/chat)
# ---------------------------------------------------------------------------

def test_chat_empty_question(client):
    response = client.post("/api/chat", json={"question": "   "})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


@patch("app.generate_llm_response")
def test_chat_with_evidence_and_context(mock_llm, client):
    """Verify follow-up chat returns grounded answers using provided evidence."""
    mock_llm.return_value = LLMResponse("The Transformer achieves 28.4 BLEU on English-to-German [P01_C0002].")

    payload = {
        "question": "What was the BLEU score on English-to-German?",
        "context": "We analyzed the original Transformer paper.",
        "evidence": [
            {
                "chunk_id": "P01_C0002",
                "paper_title": "Attention Paper",
                "section": "Results",
                "page_number": 8,
                "text": "Our model achieves 28.4 BLEU on the WMT 2014 English-to-German task."
            }
        ],
        "history": [
            {"role": "user", "content": "Tell me about the paper."},
            {"role": "assistant", "content": "It introduces Transformers."}
        ]
    }

    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == payload["question"]
    assert "28.4 BLEU" in data["answer"]
    assert "P01_C0002" in data["sources"]
    assert mock_llm.called


@patch("app.generate_llm_response")
def test_chat_missing_llm_key_handling(mock_llm, client):
    """Verify 503 response if LLM key is absent during chat."""
    mock_llm.side_effect = ValueError("No LLM API key found in .env file.")

    response = client.post(
        "/api/chat",
        json={"question": "Can you summarize the methodology?"}
    )

    assert response.status_code == 503
    assert "No LLM provider configured" in response.json()["detail"]
