# Codex prompt log

Every prompt sent to Codex during the build. Newest at the bottom.

| # | Date | Prompt (what I asked) | Result / what I changed |
|---|------|------------------------|-------------------------|
| 1 | Nov 22 | List the files in this project folder. Do not change anything. Do not open or print the .env file. | Codex listed the files and skipped .env. Confirmed Codex works in ask-for-approval mode. |
| 2 | Nov 22 | Read AGENTS.md and docs/framework.md, then create src/state.py with AgentState (TypedDict) and Pydantic models for competitors, search results and facts, plus an empty src/__init__.py. No other code, no installs. | Created src/state.py (51 lines) and src/__init__.py. Codex created the files without asking for approval because they are inside the project folder. |
| 3 | Nov 22 | Read AGENTS.md, docs/framework.md and src/state.py, then create src/tools.py with search_web and search_news using TavilySearch (basic depth, max 5 results, news topic for news), returning SearchResult objects plus an error message string. Retry once on failure, never raise, never log the API key. Add a demo block that searches "Veeva Systems". No running, no installs. | Created src/tools.py (77 lines) with search_web and search_news. Ran `python -m src.tools`: returned 5 web and 5 news results with titles and URLs, no errors. Note: news results include some stock-quote pages, so queries should be more specific. |