# Project rules for Codex

Project: Competitor analysis agent (LangChain + LangGraph, Python, Streamlit UI).

## Security
- Never open, print, or copy the contents of `.env`. API keys are read only through `os.getenv` after `load_dotenv()`.
- Never hardcode keys or put real keys in any committed file.

## Working style
- Ask before installing any new package, and add it to `requirements.txt`.
- Make small, focused changes. Explain what changed in plain English.
- Keep code simple and commented so a non-engineer can follow it.
- Do not delete files without asking.

## Project rules
- Search source: Tavily. At least one model call must go through Nebius (base URL https://api.tokenfactory.nebius.com/v1/, key NEBIUS_API_KEY).
- Every fact in the final briefing must carry a source link. Never invent facts or sources; if something is not found, say so.
- Handle errors gracefully: failed searches or model calls must not crash the run.
- A human approves the competitor list before research, and approves the briefing before it is saved.
- Test by running the code, and report what actually happened.