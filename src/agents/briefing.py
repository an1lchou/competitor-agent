"""Briefing node for rendering reviewed competitor facts as Markdown."""

from datetime import date

from src.state import AgentState


# Renders the reviewed state into a human-readable Markdown briefing.
def briefing_node(state: AgentState) -> dict:
    """Build the draft briefing without making a model call."""
    lines = [
        f"# Competitor briefing: {state['company']}",
        "",
        f"Date: {date.today().isoformat()}",
    ]
    categories = (
        ("pricing", "Pricing"),
        ("features", "Features"),
        ("positioning", "Positioning"),
        ("news", "News"),
    )
    weak_source_prefix = "weak source "
    weak_source_suffix = ": opinion or third-party site"
    weak_source_urls = {
        flag.removeprefix(weak_source_prefix).removesuffix(weak_source_suffix)
        for flag in state["review_flags"]
        if flag.startswith(weak_source_prefix) and flag.endswith(weak_source_suffix)
    }

    for competitor in state["competitors"]:
        lines.extend(
            [
                "",
                f"## {competitor.name}",
                f"Website: {competitor.website}",
                f"Reason: {competitor.reason}",
            ]
        )
        competitor_facts = [
            fact for fact in state["facts"] if fact.competitor == competitor.name
        ]
        for category, heading in categories:
            lines.extend(["", f"### {heading}"])
            category_facts = [
                fact for fact in competitor_facts if fact.category == category
            ]
            if category_facts:
                lines.extend(
                    f"- {fact.text} ([source]({fact.source_url}))"
                    f"{' (weak source)' if fact.source_url in weak_source_urls else ''}"
                    for fact in category_facts
                )
            else:
                lines.append("Not found in the sources searched.")

    lines.extend(["", "## Review notes"])
    if state["review_flags"]:
        lines.extend(f"- {flag}" for flag in state["review_flags"])
    else:
        lines.append("None")

    lines.extend(["", "## Run issues"])
    if state["errors"]:
        lines.extend(f"- {error}" for error in state["errors"])
    else:
        lines.append("None")

    return {"briefing": "\n".join(lines)}
