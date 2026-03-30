"""
agents/state.py — Shared state that flows through the QueryAnalyser LangGraph.
"""

from typing import Literal, Optional
from typing_extensions import TypedDict

from schemas.query_response import QueryResponse
from schemas.frequent_query import CanonicalQuery

class AnalyserState(TypedDict):
    query: str                               # raw user input
    llm_output: str                          # raw string returned by the LLM
    parsed: Optional[dict]                   # parsed JSON dict from llm_output
    query_response: Optional[QueryResponse]  # final typed output
    error: str                               # error message if any
    retry_count: int                         # JSON parse retry counter (max 2)
    status: Literal["ok", "error", "invalid_input","restart", "awaiting_confirmation"]
    corrections_found: list[dict]       # [{"original": "asprin", "corrected": "aspirin", "type": "drug"}]
    awaiting_confirmation: bool         # True = graph paused at interrupt()
    user_confirmation: str              # user reply — "yes" or a new name
    thread_id: str                     # Redis key to resume the right graph instance
    is_frequent_fetched: bool
    canonical_query: Optional[CanonicalQuery]
    frequent_response: Optional[str]


def initial_state(query: str, thread_id:str = "") -> AnalyserState:
    """Build a clean starting state for a new query."""
    return AnalyserState(
        query=query,
        llm_output="",
        parsed=None,
        query_response=None,
        error="",
        retry_count=0,
        status="ok",
        corrections_found=[],
        awaiting_confirmation=False,
        user_confirmation="",
        thread_id=thread_id,
        is_frequent_fetched= False,
        canonical_query= None,
        frequent_response= None
    )