"""Extraction node for converting search results into sourced facts."""

from pydantic import BaseModel

from src.agents.research import research_node
from src.llm import get_llm
from src.state import AgentState, Competitor, Fact


class FactList(BaseModel):
    """Structured facts returned by the extraction model."""

    facts: list[Fact]


# Extracts verified, sourced facts from each competitor's search results.
def extraction_node(state: AgentState) -> dict:
    """Extract facts from raw results without accepting unprovided source URLs."""
    facts: list[Fact] = []
    errors: list[str] = []

    for competitor_name, competitor_results in state["raw_results"].items():
        competitor_reason = next(
            (
                competitor.reason
                for competitor in state["competitors"]
                if competitor.name == competitor_name
            ),
            "No reason provided.",
        )
        results = competitor_results.web + competitor_results.news
        source_urls = {result.url for result in results}
        formatted_results = "\n\n".join(
            f"Title: {result.title}\nURL: {result.url}\nText: {result.text[:800]}"
            for result in results
        )
        prompt = f"""Extract facts about {competitor_name} from the provided results.

The analyzed company is {state["company"]}. {competitor_name} was selected because:
{competitor_reason}
Focus on {competitor_name}'s products and services that compete with the analyzed
company as described in that reason. Prioritize facts about those overlapping products
and services, but if the results say little about them, still extract the most relevant
facts about {competitor_name}'s main products and services instead of returning nothing.

Extract facts only in these categories: pricing, features, positioning, and news. Use
ONLY information that appears in the provided results. Every fact must have a
source_url copied exactly from one of the provided result URLs. Keep each fact to one
short sentence. For pricing, include only the price, fees, subscription plans,
licensing model, or pricing structure of the competitor's own products or services.
Do NOT treat bond or debt pricing, acquisition terms or prices, company revenue or
stock price, or government drug-pricing policy as pricing. If the results contain no
pricing information about the competitor's own products or services, return no pricing
facts at all; never guess a price. Prefer official company pages and reputable news
over blogs or analysis sites, and avoid repeating the same point in different words.
Return at most 3 facts per category.

Web and news results:
{formatted_results}
"""

        try:
            fact_list = get_llm().with_structured_output(FactList).invoke(prompt)
            facts_returned = len(fact_list.facts)
            kept_facts = 0
            dropped_unsourced = 0
            for fact in fact_list.facts:
                if fact.source_url not in source_urls:
                    errors.append(f"dropped unsourced fact for {competitor_name}")
                    dropped_unsourced += 1
                    continue
                fact.competitor = competitor_name
                facts.append(fact)
                kept_facts += 1
        except Exception as error:
            facts_returned = 0
            kept_facts = 0
            dropped_unsourced = 0
            errors.append(
                f"fact extraction model call failed for {competitor_name}: "
                f"{type(error).__name__}"
            )

        if kept_facts == 0:
            errors.append(
                f"no facts kept for {competitor_name}: {len(results)} search results, "
                f"{facts_returned} facts returned by the model, "
                f"{dropped_unsourced} dropped for unsourced url"
            )

    return {"facts": facts, "errors": errors}


if __name__ == "__main__":
    state: AgentState = {
        "company": "Test company",
        "competitors": [
            Competitor(
                name="IQVIA",
                website="https://www.iqvia.com",
                reason="test",
            )
        ],
        "competitors_approved": True,
        "raw_results": {},
        "facts": [],
        "review_flags": [],
        "errors": [],
        "briefing": "",
        "briefing_approved": False,
    }
    state.update(research_node(state))
    result = extraction_node(state)

    for fact in result["facts"]:
        print(fact.category)
        print(fact.text)
        print(fact.source_url)

    for error in result["errors"]:
        print(error)
