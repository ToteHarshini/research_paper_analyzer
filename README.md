# Agentic AI Research Paper Analyzer

An AI-powered research assistant that helps researchers discover, analyze, verify, and reason across scientific research papers using Retrieval-Augmented Generation (RAG) and Agentic AI.

## Overview

Researchers often spend significant time reading multiple research papers to understand methodologies, compare experimental results, identify limitations, and discover research gaps.

The **Agentic AI Research Paper Analyzer** aims to simplify this process by allowing users to upload research papers in PDF format and ask natural-language research questions.

The system retrieves relevant evidence, verifies claims, extracts structured findings, and generates evidence-backed research reports with citations.

## Key Features

- **PDF Upload and Processing:** Upload and extract content from scientific research papers.
- **Section Extraction:** Identify important sections such as Abstract, Introduction, Methodology, Results, Discussion, Conclusion, References, and Appendix.
- **Intelligent Chunking:** Divide documents into overlapping text chunks while preserving relevant metadata.
- **Hybrid Information Retrieval:** Combine BM25 keyword search and dense vector search to retrieve relevant passages.
- **Cross-Encoder Reranking:** Improve retrieval relevance by reranking candidate passages.
- **Agentic Research Workflow:** Decompose research questions and coordinate multiple research-processing stages.
- **Claim Verification:** Classify claims based on their supporting evidence.
- **Structured Information Extraction:** Extract methodologies, models, datasets, experimental metrics, author limitations, design trade-offs, and research gaps.
- **Evidence-Based Reports:** Generate research summaries with paragraph-level evidence references.
- **Multi-Paper Analysis:** Support comparisons across uploaded research papers.
- **Follow-up Conversations:** Allow users to ask additional questions about their research.
- **Uncertainty Awareness:** Distinguish supported findings from unsupported or uncertain claims.

## System Architecture

```text
                 USER
                   |
                   v
          React Frontend
                   |
                   v
             FastAPI Backend
                   |
                   v
             PDF Processing
                   |
                   v
            Section Extraction
                   |
                   v
              Text Chunking
                   |
                   v
             Index Creation
              /         \
             v           v
          BM25       Dense Vector
          Search       Search
              \         /
               v       v
              Hybrid Retrieval
                   |
                   v
              Cross-Encoder
                Reranking
                   |
                   v
            Agentic Workflow
                   |
        +----------+----------+
        |          |          |
        v          v          v
     Research   Verification  Structured
      Agent       Agent      Extraction
        |          |          |
        +----------+----------+
                   |
                   v
             Report Generator
                   |
                   v
          Evidence-Based Report
                   |
                   v
             React Frontend
```

## Technology Stack

### Backend

- Python 3.11+
- FastAPI
- Uvicorn
- LangGraph
- PyMuPDF
- Sentence Transformers
- ChromaDB
- rank_bm25
- Scikit-learn
- NumPy
- Pandas

### Frontend

- React
- JavaScript
- Vite
- CSS

### AI and Language Models

- Groq API
- `openai/gpt-oss-120b`
- Sentence Transformers
- Cross-Encoder models

### Development Tools

- Visual Studio Code
- Git and GitHub
- Python Virtual Environment
- pytest

## Project Structure

```text
research_paper_analyzer/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── index.css
│       └── components/
│           ├── AnalysisLoading.jsx
│           ├── CitationsTab.jsx
│           ├── ClaimsTab.jsx
│           ├── FindingsTab.jsx
│           ├── FollowUpChat.jsx
│           ├── ReportTab.jsx
│           └── ResearchInput.jsx
│
├── src/
│   ├── agents/
│   │   ├── planner.py
│   │   ├── researcher.py
│   │   ├── verifier.py
│   │   ├── structured_extractor.py
│   │   └── report_generator.py
│   │
│   ├── auth/
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── crud.py
│   │   ├── database.py
│   │   └── schemas.py
│   │
│   ├── evaluation/
│   │
│   ├── pdf_parser.py
│   ├── section_extractor.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── bm25_search.py
│   ├── hybrid_retriever.py
│   ├── reranker.py
│   ├── llm.py
│   └── research_workflow.py
│
├── tests/
│
├── data/
│   ├── uploaded_pdfs/
│   └── processed/
│
└── database/
```

*Note: This represents the intended logical organization of the project; some directories and files may vary with the current implementation.*

## Installation and Setup

### Prerequisites

Install the following:

- Python 3.11 or later
- Node.js and npm
- Git
- Visual Studio Code

### 1. Clone the Repository

```bash
git clone https://github.com/ToteHarshini/research_paper_analyzer.git

cd research_paper_analyzer
```

### 2. Create a Python Virtual Environment

```bash
python3.11 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create your local environment file:

```bash
cp .env.example .env
```

Open `.env` and configure the required API keys and settings using the variable names provided in `.env.example`.

**Important:** Never commit `.env` or expose API keys publicly.

### 5. Install Frontend Dependencies

```bash
cd frontend
npm install
```

Return to the project root when needed:

```bash
cd ..
```

## Running the Application

The backend and frontend must run in separate terminals.

### Terminal 1: Start the Backend

From the project root:

```bash
source .venv/bin/activate

uvicorn app:app --reload
```

Backend URL:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

### Terminal 2: Start the Frontend

```bash
cd frontend

npm run dev
```

Frontend URL:

http://localhost:5173

Open the frontend URL in your browser to use the application.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check backend health |
| POST | `/api/analyze` | Analyze uploaded research papers |
| POST | `/api/chat` | Ask follow-up research questions |

Interactive API documentation is available at:

http://127.0.0.1:8000/docs

## Testing

Run the backend test suite from the project root:

```bash
pytest -v
```

Run an individual test module:

```bash
python -m tests.test_parser
```

Frontend production build:

```bash
cd frontend

npm run build
```

## Example Research Questions

The application can be used to investigate questions such as:

- Explain the methodology and architecture proposed in a research paper.
- Compare experimental results across multiple papers.
- Identify the datasets and evaluation metrics used by the authors.
- Verify whether a scientific claim is supported by the uploaded evidence.
- Identify limitations explicitly acknowledged by the authors.
- Distinguish author-stated limitations from inferred research gaps.
- Identify agreements and contradictions between research findings.

## Responsible AI and Evidence Grounding

The system is designed to prioritize evidence-backed scientific reasoning.

- Important claims should be linked to relevant paper evidence.
- Unsupported information should not be presented as established fact.
- Numerical results should be grounded in the original experimental findings.
- Author-stated limitations should be distinguished from inferred research opportunities.
- Uncertainty should be communicated when sufficient evidence is unavailable.

AI-generated reports should always be checked against the original research papers.

## Future Improvements

Potential areas for further development include:

- More robust scientific table and figure extraction.
- Improved numerical benchmark retrieval.
- Graph-based relationships between papers, methods, and findings.
- Advanced contradiction and consensus detection.
- Automated citation verification.
- Comprehensive retrieval and claim-verification benchmarks.
- Improved research-gap discovery and evaluation.

## Contributors

Developed as a hackathon project focused on Agentic AI, Natural Language Processing, Information Retrieval, and scientific research assistance.

## License

A license has not yet been specified. Add an appropriate license before distributing the project for reuse.