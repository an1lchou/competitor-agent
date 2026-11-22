"""Shared state models for the competitor-analysis LangGraph run."""

from typing import Literal, TypedDict

from pydantic import BaseModel


class Competitor(BaseModel):
    """A company identified as a competitor."""

    name: str  # The competitor's name.
    website: str  # The competitor's primary website URL.
    reason: str  # Why this company is considered a competitor.


class SearchResult(BaseModel):
    """One result returned from a web or news search."""

    title: str  # The result title.
    url: str  # The source URL.
    text: str  # The result snippet or extracted text.


class CompetitorResults(BaseModel):
    """Web and news search results for one competitor."""

    web: list[SearchResult]  # Results returned from web searches.
    news: list[SearchResult]  # Results returned from news searches.


class Fact(BaseModel):
    """A sourced fact extracted during competitor research."""

    competitor: str  # The competitor this fact concerns.
    category: Literal["pricing", "features", "positioning", "news"]  # The fact category.
    text: str  # The factual claim or summary.
    source_url: str  # The URL that supports the fact.


class AgentState(TypedDict):
    """State shared between nodes in one LangGraph run."""

    company: str  # The company name entered by the analyst.
    competitors: list[Competitor]  # The discovered competitors for the company.
    competitors_approved: bool  # Whether a human approved the competitor list.
    raw_results: dict[str, CompetitorResults]  # Search results grouped by competitor name.
    facts: list[Fact]  # Sourced facts extracted from the search results.
    review_flags: list[str]  # Notes about unsourced or weak claims.
    errors: list[str]  # Notes about failed searches or model calls.
    briefing: str  # The draft competitor briefing in Markdown.
    briefing_approved: bool  # Whether a human approved the draft briefing.
