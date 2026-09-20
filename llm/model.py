import os

from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI


load_dotenv()

# The key is stored in the system environment variable "Open_router"
# (OPENROUTER_API_KEY is also accepted as a fallback)
OPENROUTER_API_KEY = os.getenv("Open_router") or os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("Open_router environment variable is not set.")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


# OpenRouter client (OpenAI-compatible) used by SchemaMapper
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)


# Models - OpenRouter slugs include the provider prefix.
# Check the exact slugs at https://openrouter.ai/models, or override
# them with the SCHEMA_MODEL / AGENT_MODEL environment variables.
SCHEMA_MODEL = os.getenv("SCHEMA_MODEL", "openai/gpt-5.6-luna")
AGENT_MODEL = os.getenv("AGENT_MODEL", "openai/gpt-5.6-terra")


def create_agent_llm():
    return ChatOpenAI(
        model=AGENT_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=0,
    )
