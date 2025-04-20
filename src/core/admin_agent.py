import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass
from openai import AsyncAzureOpenAI
from pydantic_ai import RunContext
from pydantic_ai.agent import Agent
from database import Database

sys_prompt = """

"""


@dataclass
class Deps:
    openai: AsyncAzureOpenAI
    db: Database


agent = Agent(system_prompt=sys_prompt, deps_type=Deps)


@agent.tool
async def fetch_entire_kb(context: RunContext[Deps]) -> dict[str, str]:
    """Returns the entire knowledge base as key-value pairs"""
    # TODO


@agent.tool
async def fetch_personal_website(context: RunContext[Deps]) -> str:
    """Returns the contents of your client's personal website"""
    # TODO


@agent.tool
async def fetch_resume(context: RunContext[Deps]) -> str:
    """Returns the contents of your client's resume/CV"""
    # TODO


@agent.tool
async def query_kb(
    context: RunContext[Deps], query: str
) -> dict[str, str] | list[str] | str:
    """
    Queries into the knowledge base
    Args:
        - query: query text
    Returns:
        - If the search query matches a key in the knowledge base the values
        corresponding to that key is returned (or)
        - In the case of no exact matches the top 3 most relevant key-value pairs
        are returned.
    """
    # TODO
