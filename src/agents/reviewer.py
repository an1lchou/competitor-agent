"""Reviewer node for validating extracted competitor facts."""

from typing import Literal

from pydantic import BaseModel

from src.agents.extraction import extraction_node
from src.agents.research import research_node
from src.llm import get_llm
from src.state import AgentState, Competitor, Fact


class FactVerdict(BaseModel):
    """A review decision for one numbered fact."""

    index: int
    verdict: Literal["keep", "drop"]
    reason: str
    weak_source: bool


class ReviewResult(BaseModel):
    """Structured verdicts returned by the reviewer model."""

    verdicts: list[FactVerdict]


# Reviews sourced facts and returns only those supported by their source text.
def reviewer_node(state: AgentState) -> dict:
    """Validate facts per competitor while retaining facts that cannot be reviewed."""
    facts_by_competitor: dict[str, list[Fact]] = {}
    for fact in state["facts"]:
        facts_by_competitor.setdefault(fact.competitor, []).append(fact)

    kept_facts: list[Fact] = []
    review_flags: list[str] = []
    errors: list[str] = []
    reviewed_competitors: set[str] = set()
    weak_source_urls: set[str] = set()

    for competitor_name, competitor_results in state["raw_results"].items():
        competitor_facts = facts_by_competitor.get(competitor_name, [])
        source_texts = {
            result.url: result.text
            for result in competitor_results.web + competitor_results.news
        }
        numbered_facts = "\n\n".join(
            f"{index}. Category: {fact.category}\nFact: {fact.text}\n"
            f"Source URL: {fact.source_url}\n"
            f"Source text: {source_texts.get(fact.source_url, '')}"
            for index, fact in enumerate(competitor_facts, start=1)
        )
        prompt = f"""Review every numbered fact about {competitor_name} against its source text.

Give a verdict for every fact. Drop a fact if its source text does not support it, if
it is in the wrong category, or if it repeats another fact. A pricing fact is wrong
unless it concerns the price, fees, or pricing model of {competitor_name}'s own
products or services; examples to drop include bond pricing, acquisition terms, and
revenue. Otherwise keep the fact. Set weak_source to true when the source is a
third-party blog, analysis site, or aggregator rather than {competitor_name}'s own
site or a reputable news outlet. Give a short reason for each verdict.

Facts and source texts:
{numbered_facts}
"""

        try:
            review_result = get_llm().with_structured_output(ReviewResult).invoke(prompt)
            verdicts = {verdict.index: verdict for verdict in review_result.verdicts}
            for index, fact in enumerate(competitor_facts, start=1):
                verdict = verdicts.get(index)
                if verdict is None:
                    kept_facts.append(fact)
                    continue

                if verdict.weak_source and fact.source_url not in weak_source_urls:
                    weak_source_urls.add(fact.source_url)
                    review_flags.append(
                        f"weak source {fact.source_url}: opinion or third-party site"
                    )

                if verdict.verdict == "drop":
                    review_flags.append(
                        f"dropped {competitor_name} {fact.category}: {verdict.reason}"
                    )
                else:
                    kept_facts.append(fact)
            reviewed_competitors.add(competitor_name)
        except Exception as error:
            kept_facts.extend(competitor_facts)
            errors.append(
                f"fact review model call failed for {competitor_name}: "
                f"{type(error).__name__}"
            )
            review_flags.append(f"review failed for {competitor_name}: facts not reviewed")
            reviewed_competitors.add(competitor_name)

    for competitor_name, competitor_facts in facts_by_competitor.items():
        if competitor_name not in reviewed_competitors:
            kept_facts.extend(competitor_facts)

    return {"facts": kept_facts, "review_flags": review_flags, "errors": errors}


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
    state.update(extraction_node(state))
    facts_before_review = len(state["facts"])
    state.update(reviewer_node(state))

    print(f"facts before review: {facts_before_review}")
    print(f"facts after review: {len(state['facts'])}")
    for fact in state["facts"]:
        print(fact.category)
        print(fact.text)
        print(fact.source_url)

    for review_flag in state["review_flags"]:
        print(review_flag)

    for error in state["errors"]:
        print(error)
