"""Research node for gathering competitor web and news results."""

from src.state import AgentState, Competitor, CompetitorResults
from src.tools import search_news, search_web


# Researches every approved competitor and groups the returned search results.
def research_node(state: AgentState) -> dict:
    """Collect web and news results for each competitor in the state."""
    competitors = state["competitors"]
    if not competitors:
        return {"raw_results": {}, "errors": ["no competitors to research"]}

    company = state.get("company", "").strip()
    raw_results: dict[str, CompetitorResults] = {}
    errors: list[str] = []

    for competitor in competitors:
        pricing_query = (
            f"{competitor.name} pricing plans cost for products competing with {company}"
            if company
            else f"{competitor.name} pricing plans cost"
        )
        feature_query = (
            f"{competitor.name} products features positioning versus {company}"
            if company
            else f"{competitor.name} products features positioning"
        )
        pricing_results, pricing_error = search_web(
            pricing_query
        )
        feature_results, feature_error = search_web(
            feature_query
        )
        overview_results, overview_error = search_web(
            f"{competitor.name} products features positioning overview"
        )
        news_results, news_error = search_news(f"{competitor.name} announcement")

        errors.extend(
            error
            for error in (pricing_error, feature_error, overview_error, news_error)
            if error
        )

        seen_urls: set[str] = set()
        web_results = []
        for result in pricing_results + feature_results + overview_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                web_results.append(result)

        raw_results[competitor.name] = CompetitorResults(
            web=web_results,
            news=news_results,
        )
        if not web_results and not news_results:
            errors.append(f"no search results for {competitor.name}")

    return {"raw_results": raw_results, "errors": errors}


if __name__ == "__main__":
    result = research_node(
        {
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
    )
    for competitor_name, competitor_results in result["raw_results"].items():
        print(competitor_name)
        for result_type, results in (
            ("web", competitor_results.web),
            ("news", competitor_results.news),
        ):
            print(f"{result_type}: {len(results)} results")
            for search_result in results[:3]:
                print(search_result.title)
                print(search_result.url)

    for error in result["errors"]:
        print(error)
