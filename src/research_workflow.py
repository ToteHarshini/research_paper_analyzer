from typing import TypedDict, Any

from langgraph.graph import StateGraph, END

from src.agents.structured_extractor import extract_structured_findings
from src.agents.planner import generate_subquestions
from src.agents.researcher import research_subquestions
from src.agents.verifier import extract_claims, verify_claims
from src.agents.report_generator import generate_final_report
from src.reranker import rerank_results


# Shared state passed between all workflow nodes
class ResearchState(TypedDict, total=False):
    question: str
    index: Any
    chunks: list

    subquestions: list
    retrieved_results: list
    reranked_results: list

    claims: list
    verified_claims: list
    final_report: str


# NODE 1: Planner Agent
def planner_node(state: ResearchState):

    print("\n--- PLANNER AGENT ---")

    subquestions = generate_subquestions(
        state["question"]
    )

    print("\nGenerated subquestions:")

    for i, subquestion in enumerate(subquestions, start=1):
        print(f"{i}. {subquestion}")

    return {
        "subquestions": subquestions
    }


# NODE 2: Researcher Agent
def researcher_node(state: ResearchState):

    print("\n--- RESEARCHER AGENT ---")

    results = research_subquestions(
        index=state["index"],
        chunks=state["chunks"],
        subquestions=state["subquestions"],
        top_k=5
    )

    print(f"Retrieved {len(results)} unique chunks.")

    return {
        "retrieved_results": results
    }


# NODE 3: Cross-Encoder Reranker
def reranker_node(state: ResearchState):

    print("\n--- RERANKER ---")

    results = rerank_results(
        query=state["question"],
        results=state["retrieved_results"],
        top_k=10
    )

    print(f"Selected {len(results)} relevant chunks.")

    return {
        "reranked_results": results
    }


# NODE 4: Claim Extraction
def claim_extraction_node(state: ResearchState):

    print("\n--- CLAIM EXTRACTION ---")

    claims = extract_claims(
        question=state["question"],
        evidence=state["reranked_results"]
    )

    print(f"Extracted {len(claims)} claims.")

    return {
        "claims": claims
    }


# NODE 5: Verifier Agent
def verifier_node(state: ResearchState):

    print("\n--- VERIFIER AGENT ---")

    verified_claims = verify_claims(
        question=state["question"],
        claims=state["claims"],
        evidence=state["reranked_results"]
    )

    for item in verified_claims:
        print(f"\nClaim: {item['claim']}")
        print(f"Status: {item['status']}")
        print(f"Citations: {item['citations']}")

    return {
        "verified_claims": verified_claims
    }

class ResearchState(TypedDict, total=False):
    question: str
    index: Any
    chunks: list

    subquestions: list
    retrieved_results: list
    reranked_results: list

    claims: list
    verified_claims: list
    structured_findings: list

    final_report: str

# NODE 6: Structured Research Agent
def structured_extraction_node(state: ResearchState):

    print("\n--- STRUCTURED RESEARCH AGENT ---")

    findings = extract_structured_findings(
        question=state["question"],
        evidence=state["reranked_results"]
    )

    print(f"Extracted {len(findings)} structured findings.")

    for item in findings:
        print(f"\nCategory: {item['category']}")
        print(f"Finding: {item['finding']}")

    return {
        "structured_findings": findings
    }
# NODE 6: Report Generator Agent
def report_generator_node(state: ResearchState):

    print("\n--- REPORT GENERATOR AGENT ---")

    report = generate_final_report(
        question=state["question"],
        evidence=state["reranked_results"],
        verified_claims=state["verified_claims"]
    )

    print("\nFinal report generated.")

    return {
        "final_report": report
    }


# Build the LangGraph workflow
def build_research_graph():

    workflow = StateGraph(ResearchState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("reranker", reranker_node)
    workflow.add_node("claim_extraction", claim_extraction_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("structured_extraction", structured_extraction_node)
    workflow.add_node("report_generator", report_generator_node)

    workflow.set_entry_point("planner")

    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "reranker")
    workflow.add_edge("reranker", "claim_extraction")
    workflow.add_edge("claim_extraction", "verifier")
    workflow.add_edge("verifier", "structured_extraction")
    workflow.add_edge("structured_extraction", "report_generator")
    workflow.add_edge("report_generator", END)

    return workflow.compile()


# Run the complete agentic research system
def run_agentic_research(question, index, chunks):

    graph = build_research_graph()

    initial_state = {
        "question": question,
        "index": index,
        "chunks": chunks
    }

    result = graph.invoke(initial_state)

    return result
