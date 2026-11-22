# Codex prompt log

Every prompt sent to Codex during the build. Newest at the bottom.

| # | Date | Prompt (what I asked) | Result / what I changed |
|---|------|------------------------|-------------------------|
| 1 | Nov 22 | List the files in this project folder. Do not change anything. Do not open or print the .env file. | Codex listed the files and skipped .env. Confirmed Codex works in ask-for-approval mode. |
| 2 | Nov 22 | Read AGENTS.md and docs/framework.md, then create src/state.py with AgentState (TypedDict) and Pydantic models for competitors, search results and facts, plus an empty src/__init__.py. No other code, no installs. | Created src/state.py (51 lines) and src/__init__.py. Codex created the files without asking for approval because they are inside the project folder. |