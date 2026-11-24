"""Save node for persisting a human-approved briefing."""

from src.state import AgentState
from src.tools import save_briefing


# Saves the briefing only after explicit human approval.
def save_node(state: AgentState) -> dict:
    """Persist an approved briefing and report its file path or save error."""
    if state["briefing_approved"] is not True:
        return {"errors": ["briefing not approved, nothing saved"], "saved_path": ""}

    saved_path, error = save_briefing(state["company"], state["briefing"])
    return {"saved_path": saved_path, "errors": [error] if error else []}
