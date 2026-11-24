"""Discovery node for identifying a company's direct competitors."""

from pydantic import BaseModel

from src.llm import get_llm
from src.state import AgentState, Competitor
from src.tools import search_web


class CompetitorList(BaseModel):
    """Structured competitors returned by the discovery model."""

    competitors: list[Competitor]


# Finds direct competitors from two web searches and structured model output.
def discovery_node(state: AgentState) -> dict:
    """Discover up to three direct competitors for the selected company."""
    company = state["company"]
    first_results, first_error = search_web(f"{company} top competitors")
    second_results, second_error = search_web(f"{company} alternatives competitors")

    errors = [error for error in (first_error, second_error) if error]
    results = first_results + second_results
    if not results:
        return {"competitors": [], "errors": errors}

    search_results = "\n\n".join(
        f"Title: {result.title}\nURL: {result.url}\nText: {result.text}"
        for result in results
    )
    prompt = f"""Identify direct competitors of {company} using only these search results.

Pick exactly the 3 most relevant direct competitors, if three are available. Use ONLY
companies named in the search results. For each competitor, give a website URL taken
from the results, or that company's well-known official domain only when that domain is
shown in the results. Give a one-sentence reason. Never invent a company, and never
include {company} itself.

Search results:
{search_results}
"""

    try:
        competitor_list = get_llm().with_structured_output(CompetitorList).invoke(prompt)
        competitors = [
            competitor
            for competitor in competitor_list.competitors
            if competitor.name.casefold() != company.casefold()
        ][:3]
        return {"competitors": competitors, "errors": errors}
    except Exception as error:
        errors.append(f"competitor discovery model call failed: {type(error).__name__}")
        return {"competitors": [], "errors": errors}


if __name__ == "__main__":
    result = discovery_node(
        {
            "company": "Veeva Systems",
            "competitors": [],
            "competitors_approved": False,
            "raw_results": {},
            "facts": [],
            "review_flags": [],
            "errors": [],
            "briefing": "",
            "briefing_approved": False,
        }
    )
    for competitor in result["competitors"]:
        print(competitor.name)
        print(competitor.website)
        print(competitor.reason)

    for error in result["errors"]:
        print(error)
