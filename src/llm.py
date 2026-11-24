"""Nebius Token Factory language-model connection helpers."""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from openai import OpenAI


NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"

load_dotenv()


# Creates the configured Nebius chat model for LangChain use.
def get_llm() -> ChatOpenAI:
    """Return a Nebius-backed ChatOpenAI instance."""
    api_key = os.getenv("NEBIUS_API_KEY", "").strip()
    model = os.getenv("NEBIUS_MODEL", "").strip()

    if not api_key:
        raise ValueError("NEBIUS_API_KEY is required.")
    if not model:
        raise ValueError("NEBIUS_MODEL is required.")

    return ChatOpenAI(
        api_key=api_key,
        model=model,
        base_url=NEBIUS_BASE_URL,
        temperature=0,
        timeout=60,
        max_retries=1,
    )


# Lists the model IDs available through the Nebius Token Factory API.
def list_models() -> list[str]:
    """Return available Nebius model IDs in alphabetical order."""
    client = OpenAI(
        api_key=os.getenv("NEBIUS_API_KEY", "").strip(),
        base_url=NEBIUS_BASE_URL,
    )
    return sorted(model.id for model in client.models.list().data)


if __name__ == "__main__":
    for model_id in list_models():
        print(model_id)
