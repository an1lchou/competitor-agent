# Competitor Analysis Agent: One-liner and Framework

## One-liner
My agent helps a pharma strategy analyst build competitor briefings in a Streamlit app, replacing about 3 hours of manual research per company. It finds 3 competitors, researches each one, and drafts a sourced briefing on its own using 4 tools, hands off to a human to approve the competitor list and the final briefing, and I'll know it works when an analyst gets a usable briefing in under 10 minutes for 3 of 3 test companies.

## Framework

| Field | Answer |
|---|---|
| Agent goal | Takes a company name and produces a sourced competitor briefing on its top 3 competitors. |
| Where people use it | A Streamlit web app on the analyst's computer. |
| Steps, in order | 1) Analyst enters a company. 2) Discovery agent finds the top 3 competitors. 3) Human approves or edits the list. 4) Research agent searches web and news for each. 5) Extraction agent pulls pricing, features, positioning and news, each with a source link. 6) Reviewer agent flags any unsourced claim. 7) Human approves the briefing. 8) Briefing is saved as a markdown file. |
| What it can do (4 tools) | Tavily web search (look-up), Tavily news search (look-up), Nebius model for extraction and review (look-up/analysis), save briefing file (changes something). |
| What it remembers | Within one run: company, competitor list, search results, extracted facts, errors and draft briefing, held in LangGraph state with a checkpointer so a run can pause for approval and resume. Across sessions: only the saved briefings. |
| What it must never do | Invent facts or sources, include a claim without a source link, save a briefing without human approval, or expose API keys. |
| Human-in-the-loop | Two points: after discovery (approve or edit the competitor list) and before saving (approve or reject the briefing, with a note). |
| When something breaks | A failed search or model call is retried once, then skipped with a visible "not found" note in the briefing. The run never crashes, and the analyst sees which parts are missing. |
| How you know it worked | A usable briefing in under 10 minutes for 3 of 3 test companies, with every fact traceable to a source. |