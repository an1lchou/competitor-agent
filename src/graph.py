"""LangGraph workflow and console driver for competitor briefings."""

from collections.abc import Callable

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from src.agents.briefing import briefing_node
from src.agents.discovery import discovery_node
from src.agents.extraction import extraction_node
from src.agents.research import research_node
from src.agents.reviewer import reviewer_node
from src.agents.save import save_node
from src.state import AgentState, Competitor


# Wraps ordinary graph nodes so unexpected failures become state errors.
def safe_node(name: str, fn: Callable[[AgentState], dict]) -> Callable[[AgentState], dict]:
    """Return a node wrapper that converts exceptions into error updates."""
    def wrapped(state: AgentState) -> dict:
        try:
            return fn(state)
        except Exception as error:
            return {"errors": [f"{name} crashed: {type(error).__name__}"]}

    return wrapped


# Pauses the graph for a human decision about discovered competitors.
def approve_competitors(state: AgentState) -> dict:
    """Interrupt for competitor approval and apply an optional edited list."""
    resume = interrupt(
        {
            "type": "approve_competitors",
            "competitors": [competitor.model_dump() for competitor in state["competitors"]],
        }
    )
    response = resume if isinstance(resume, dict) else {}
    if response.get("approved") is True:
        edited_competitors = response.get("competitors")
        competitors = (
            [Competitor(**competitor) for competitor in edited_competitors]
            if isinstance(edited_competitors, list)
            else state["competitors"]
        )
        return {"competitors": competitors, "competitors_approved": True}
    return {
        "competitors_approved": False,
        "errors": ["competitor list rejected by the human"],
    }


# Pauses the graph for a human decision about the generated briefing.
def approve_briefing(state: AgentState) -> dict:
    """Interrupt for briefing approval and apply optional edited Markdown."""
    resume = interrupt(
        {
            "type": "approve_briefing",
            "briefing": state["briefing"],
            "review_flags": state["review_flags"],
            "errors": state["errors"],
        }
    )
    response = resume if isinstance(resume, dict) else {}
    edited_briefing = response.get("briefing")
    return {
        "briefing_approved": response.get("approved") is True,
        "briefing": (
            edited_briefing if isinstance(edited_briefing, str) else state["briefing"]
        ),
    }


# Directs the graph away from approval when discovery found no competitors.
def after_discovery(state: AgentState) -> str:
    """Choose approval or termination after competitor discovery."""
    return "approve_competitors" if state["competitors"] else END


# Ends a run when the human rejects the discovered competitor list.
def after_competitor_approval(state: AgentState) -> str:
    """Choose research or termination after competitor approval."""
    return "research" if state["competitors_approved"] else END


# Builds the complete, checkpointer-backed LangGraph workflow.
def build_graph(checkpointer=None):
    """Compile and return the competitor-briefing graph."""
    graph = StateGraph(AgentState)
    graph.add_node("discovery", safe_node("discovery", discovery_node))
    graph.add_node("approve_competitors", approve_competitors)
    graph.add_node("research", safe_node("research", research_node))
    graph.add_node("extraction", safe_node("extraction", extraction_node))
    graph.add_node("reviewer", safe_node("reviewer", reviewer_node))
    graph.add_node("briefing", safe_node("briefing", briefing_node))
    graph.add_node("approve_briefing", approve_briefing)
    graph.add_node("save", safe_node("save", save_node))

    graph.add_edge(START, "discovery")
    graph.add_conditional_edges("discovery", after_discovery)
    graph.add_conditional_edges("approve_competitors", after_competitor_approval)
    graph.add_edge("research", "extraction")
    graph.add_edge("extraction", "reviewer")
    graph.add_edge("reviewer", "briefing")
    graph.add_edge("briefing", "approve_briefing")
    graph.add_edge("approve_briefing", "save")
    graph.add_edge("save", END)

    return graph.compile(checkpointer=checkpointer)


# Creates a complete, empty state for a new company briefing run.
def new_state(company: str) -> dict:
    """Return the initial AgentState values for a company."""
    return {
        "company": company,
        "competitors": [],
        "competitors_approved": False,
        "raw_results": {},
        "facts": [],
        "review_flags": [],
        "errors": [],
        "briefing": "",
        "briefing_approved": False,
        "saved_path": "",
    }


if __name__ == "__main__":
    company = input("Company name: ").strip()
    app = build_graph(MemorySaver())
    config = {"configurable": {"thread_id": "console-briefing"}}
    result = app.invoke(new_state(company), config)

    while result.get("__interrupt__"):
        payload = result["__interrupt__"][0].value
        if payload["type"] == "approve_competitors":
            print("\nDiscovered competitors:")
            for index, competitor in enumerate(payload["competitors"], start=1):
                print(f"{index}. {competitor['name']}")
                print(f"   Website: {competitor['website']}")
                print(f"   Reason: {competitor['reason']}")
        else:
            print("\nDraft briefing:\n")
            print(payload["briefing"])
            print("\nReview flags:")
            for flag in payload["review_flags"]:
                print(f"- {flag}")
            print("\nErrors:")
            for error in payload["errors"]:
                print(f"- {error}")

        approved = input("Approve? (y/n) ").strip().lower() == "y"
        result = app.invoke(Command(resume={"approved": approved}), config)

    print(f"Saved path: {result.get('saved_path', '')}")
    for error in result.get("errors", []):
        print(f"- {error}")
