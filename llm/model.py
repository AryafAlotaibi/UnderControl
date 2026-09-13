import os

from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set.")


# OpenAI client used by SchemaMapper
client = OpenAI(
    api_key=OPENAI_API_KEY
)


# Models
SCHEMA_MODEL = "gpt-5.6-luna"
AGENT_MODEL = "gpt-5.6-terra"


def create_agent_llm():
    return ChatOpenAI(
        model=AGENT_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0,
    )