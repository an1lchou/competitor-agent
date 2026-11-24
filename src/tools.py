"""Tavily search helpers for competitor research."""

import os
import re
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from langchain_tavily import TavilySearch

from src.state import SearchResult


load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# Searches Tavily's general web index and returns safe, structured results.
def search_web(query: str) -> tuple[list[SearchResult], str | None]:
    """Search the web, retrying once if Tavily returns an error."""
    for attempt in range(2):
        try:
            response = TavilySearch(
                tavily_api_key=TAVILY_API_KEY,
                search_depth="basic",
                max_results=5,
            ).invoke({"query": query})
            results = [
                SearchResult(
                    title=str(result.get("title", "")),
                    url=str(result["url"]),
                    text=str(result.get("content", "")),
                )
                for result in response["results"]
                if result.get("url")
            ]
            return results, None
        except Exception as error:
            if attempt == 1:
                return [], f"web search failed for '{query}': {type(error).__name__}"

    return [], f"web search failed for '{query}': unknown error"


# Searches Tavily's news index and returns safe, structured results.
def search_news(query: str) -> tuple[list[SearchResult], str | None]:
    """Search the news, retrying once if Tavily returns an error."""
    for attempt in range(2):
        try:
            response = TavilySearch(
                tavily_api_key=TAVILY_API_KEY,
                search_depth="basic",
                max_results=5,
                topic="news",
            ).invoke({"query": query})
            results = [
                SearchResult(
                    title=str(result.get("title", "")),
                    url=str(result["url"]),
                    text=str(result.get("content", "")),
                )
                for result in response["results"]
                if result.get("url")
            ]
            return results, None
        except Exception as error:
            if attempt == 1:
                return [], f"news search failed for '{query}': {type(error).__name__}"

    return [], f"news search failed for '{query}': unknown error"


# Saves an approved briefing as a dated Markdown file.
def save_briefing(company: str, briefing: str) -> tuple[str, str | None]:
    """Save a briefing file and return its path or a safe error message."""
    try:
        filename_company = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")
        filename_company = filename_company or "briefing"
        directory = Path("briefings")
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{filename_company}_{date.today().isoformat()}.md"
        path.write_text(briefing, encoding="utf-8")
        return str(path), None
    except Exception as error:
        return "", f"briefing save failed for '{company}': {type(error).__name__}"


if __name__ == "__main__":
    for result in search_web("Veeva Systems")[0]:
        print(result.title)
        print(result.url)

    for result in search_news("Veeva Systems")[0]:
        print(result.title)
        print(result.url)
