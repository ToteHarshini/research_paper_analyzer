import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from src.bm25_search import create_bm25_index
from src.chunker import chunk_pages
from src.db.schemas import (
    ChatRequest,
    ChatResponse,
    ClaimVerification,
    HealthResponse,
    ResearchQueryResponse,
    RetrievedEvidenceItem,
    StructuredFinding,
)
from src.llm import generate_llm_response, get_provider
from src.pdf_parser import extract_pdf_text
from src.research_workflow import run_agentic_research
from src.vector_store import search_chunks, store_chunks

# Directory configuration
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "data" / "uploaded_pdfs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Maximum file upload size: 50 MB
MAX_FILE_SIZE = 50 * 1024 * 1024

app = FastAPI(
    title="Agentic AI Research Paper Analyzer",
    description="Multi-agent academic literature analysis powered by LangGraph, BM25, and ChromaDB.",
    version="1.0.0",
)

# CORS configuration for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 1. HEALTH ENDPOINT
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check application status and detect active LLM provider.
    """
    provider = None
    try:
        provider = get_provider()
    except Exception:
        provider = None

    db_connected = False
    try:
        from src.db.database import test_connection
        db_connected = await run_in_threadpool(test_connection)
    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        llm_provider=provider,
        database_connected=db_connected,
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# 2. RESEARCH PAPER ANALYSIS ENDPOINT
# ---------------------------------------------------------------------------

@app.post("/api/analyze", response_model=ResearchQueryResponse)
async def analyze_papers(
    question: str = Form(..., description="The research question to analyze"),
    files: list[UploadFile] = File(..., description="One or more PDF research papers"),
):
    """
    Accept a research question and multiple PDF research papers, parse and chunk the
    content, build vector & BM25 indexes, execute the LangGraph agentic research
    workflow, and return an evidence-backed synthesized research report.
    """
    # 1. Validate research question
    cleaned_question = question.strip()
    if not cleaned_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research question cannot be empty.",
        )

    # 2. Validate files list
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one PDF file must be provided.",
        )

    saved_file_paths: list[tuple[str, str, Path]] = []  # (paper_id, paper_title, Path)

    # 3. Validate and persist uploaded PDF files
    for idx, uploaded_file in enumerate(files, start=1):
        filename = uploaded_file.filename or f"uploaded_paper_{idx}.pdf"
        clean_filename = Path(filename).name

        if not clean_filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' is not a PDF. Only PDF files are supported.",
            )

        content = await uploaded_file.read()

        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' is empty.",
            )

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' exceeds the maximum allowed size of 50MB.",
            )

        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' is not a valid PDF document (missing PDF header).",
            )

        paper_id = f"PAPER{idx:02d}"
        paper_title = Path(clean_filename).stem.replace("_", " ").title()
        unique_name = f"{uuid.uuid4().hex[:8]}_{clean_filename}"
        dest_path = UPLOAD_DIR / unique_name

        dest_path.write_bytes(content)
        saved_file_paths.append((paper_id, paper_title, dest_path))

    # 4. Parse PDFs and chunk text
    all_chunks: list[dict[str, Any]] = []

    for paper_id, paper_title, file_path in saved_file_paths:
        try:
            pages = await run_in_threadpool(extract_pdf_text, str(file_path))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Failed to parse PDF '{file_path.name}': {str(exc)}",
            ) from exc

        if not pages or not any(p["text"].strip() for p in pages):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not extract any text from '{paper_title}'. The document may be scanned or empty.",
            )

        chunks = chunk_pages(
            pages=pages,
            paper_id=paper_id,
            paper_title=paper_title,
            chunk_size=1000,
            overlap=200,
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate text chunks from the uploaded documents.",
        )

    # 5. Build indexes (Vector Store & BM25)
    try:
        await run_in_threadpool(store_chunks, all_chunks)
        bm25_index = await run_in_threadpool(create_bm25_index, all_chunks)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build search indexes: {str(exc)}",
        ) from exc

    # 6. Execute LangGraph Agentic Research Workflow
    try:
        workflow_output = await run_in_threadpool(
            run_agentic_research,
            question=cleaned_question,
            index=bm25_index,
            chunks=all_chunks,
        )
    except ValueError as exc:
        # Typical when LLM keys are missing
        if "No LLM API key found" in str(exc) or "API key not found" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No LLM provider configured. Please set GROQ_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY in your .env file.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research agent workflow error: {str(exc)}",
        ) from exc
    except Exception as exc:
        error_msg = str(exc)
        if "429" in error_msg or "rate_limit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="LLM rate limit exceeded. Please wait a moment before trying again.",
            ) from exc
        if "Connection error" in error_msg or "nodename nor servname provided" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to connect to the external LLM service. Please verify your internet connection or API status.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during research analysis: {error_msg}",
        ) from exc

    # 7. Format verified claims
    formatted_claims: list[ClaimVerification] = []
    for item in workflow_output.get("verified_claims", []):
        formatted_claims.append(
            ClaimVerification(
                claim=item.get("claim", ""),
                status=item.get("status", "insufficient_evidence"),
                reason=item.get("reason", ""),
                citations=item.get("citations", []),
            )
        )

    # 8. Format structured findings
    formatted_findings: list[StructuredFinding] = []
    for item in workflow_output.get("structured_findings", []):
        formatted_findings.append(
            StructuredFinding(
                category=item.get("category", "methodology"),
                finding=item.get("finding", ""),
                sources=item.get("sources", []),
            )
        )

    # 9. Format evidence passages
    evidence_items: list[RetrievedEvidenceItem] = []
    for item in workflow_output.get("reranked_results", []):
        chunk = item.get("chunk", {})
        evidence_items.append(
            RetrievedEvidenceItem(
                chunk_id=chunk.get("chunk_id", ""),
                paper_id=chunk.get("paper_id"),
                paper_title=chunk.get("paper_title"),
                section=chunk.get("section"),
                page_number=chunk.get("page_number"),
                text=chunk.get("text"),
                reranker_score=item.get("reranker_score"),
            )
        )

    return ResearchQueryResponse(
        question=cleaned_question,
        subquestions=workflow_output.get("subquestions", []),
        final_report=workflow_output.get("final_report", ""),
        verified_claims=formatted_claims,
        structured_findings=formatted_findings,
        evidence=evidence_items,
        conversation_id=None,
    )


# ---------------------------------------------------------------------------
# 3. FOLLOW-UP CHAT ENDPOINT
# ---------------------------------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse)
async def chat_followup(request: ChatRequest):
    """
    Accept a follow-up question and optional research context/evidence,
    generating an evidence-grounded answer based on the analyzed literature.
    """
    cleaned_question = request.question.strip()
    if not cleaned_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Follow-up question cannot be empty.",
        )

    evidence_text_parts: list[str] = []
    sources: list[str] = []

    # Use explicitly passed evidence if present
    if request.evidence:
        for item in request.evidence:
            chunk = item.get("chunk", item)
            chunk_id = chunk.get("chunk_id", "Unknown")
            paper = chunk.get("paper_title", "Paper")
            section = chunk.get("section", "Section")
            page = chunk.get("page_number", "?")
            text = chunk.get("text", "")

            evidence_text_parts.append(
                f"Source ID: {chunk_id} | Paper: {paper} | Section: {section} | Page: {page}\nText: {text}"
            )
            sources.append(chunk_id)

    # If no explicit evidence, query the persistent ChromaDB collection
    if not evidence_text_parts:
        try:
            results = await run_in_threadpool(search_chunks, query=cleaned_question, n_results=5)
            if results and results.get("documents") and results["documents"][0]:
                for doc, meta, cid in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["ids"][0],
                ):
                    evidence_text_parts.append(
                        f"Source ID: {cid} | Paper: {meta.get('paper_title', 'Unknown')} | "
                        f"Section: {meta.get('section', 'Unknown')} | Page: {meta.get('page_number', '?')}\n"
                        f"Text: {doc}"
                    )
                    sources.append(cid)
        except Exception:
            # Vector store query may be empty if no papers uploaded yet
            pass

    evidence_block = (
        "\n\n---\n\n".join(evidence_text_parts)
        if evidence_text_parts
        else "No specific paper passages provided."
    )

    context_block = f"\nPrevious Research Summary:\n{request.context}\n" if request.context else ""

    history_block = ""
    if request.history:
        turns = []
        for turn in request.history[-6:]:  # Keep last 3 exchanges
            role = turn.get("role", "user").capitalize()
            content = turn.get("content", "")
            turns.append(f"{role}: {content}")
        history_block = "\nRecent Conversation:\n" + "\n".join(turns) + "\n"

    system_instruction = """
You are a precise scientific research assistant answering follow-up questions about research papers.

Guidelines:
1. Answer the question using ONLY the provided research evidence and context.
2. Cite sources using Source IDs (e.g. [PAPER01_C0001]) or paper titles where applicable.
3. If the evidence does not contain sufficient facts to answer the question, explicitly state that rather than speculating.
4. Keep the answer clear, rigorous, and directly helpful.
"""

    prompt = f"""
{history_block}
{context_block}
Retrieved Literature Evidence:
{evidence_block}

Follow-up Question:
{cleaned_question}

Provide an evidence-grounded answer:
"""

    try:
        llm_response = await run_in_threadpool(
            generate_llm_response,
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.2,
            max_output_tokens=2000,
        )
    except ValueError as exc:
        if "No LLM API key found" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No LLM provider configured. Please set GROQ_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation error: {str(exc)}",
        ) from exc
    except Exception as exc:
        error_msg = str(exc)
        if "429" in error_msg or "rate_limit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="LLM rate limit exceeded. Please wait a moment before trying again.",
            ) from exc
        if "Connection error" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Connection error contacting LLM provider.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate chat response: {error_msg}",
        ) from exc

    return ChatResponse(
        question=cleaned_question,
        answer=llm_response.text,
        sources=list(set(sources)),
    )
