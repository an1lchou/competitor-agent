import os
from dotenv import load_dotenv

load_dotenv()

tav = os.getenv("TAVILY_API_KEY", "").strip()
neb = os.getenv("NEBIUS_API_KEY", "").strip()

print("Tavily key set:", bool(tav))
print("Nebius key set:", bool(neb))

if tav:
    try:
        from langchain_tavily import TavilySearch
        r = TavilySearch(max_results=1).invoke({"query": "Veeva Systems"})
        print("Tavily OK, results:", len(r.get("results", [])))
    except Exception as e:
        print("Tavily FAILED:", type(e).__name__)

if neb:
    try:
        from openai import OpenAI
        c = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=neb)
        print("Nebius OK, models available:", len(list(c.models.list())))
    except Exception as e:
        print("Nebius FAILED:", type(e).__name__)