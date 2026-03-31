from typing import Literal, Optional
from typing_extensions import TypedDict

from schemas.analyse_query import QueryResponse


class AnalyserState(TypedDict):
    query: str                               
    llm_output: str                          
    parsed: Optional[dict]                   
    query_response: Optional[QueryResponse]  
    error: str                               
    retry_count: int                         
    status: Literal["ok", "error", "invalid_input", "restart", "awaiting_confirmation"]
    corrections_found: list[dict]            
    awaiting_confirmation: bool             
    user_confirmation: str                   
    clarification_needed: bool               
    clarification_message: str               
    thread_id: str                           
    final_answer: str                        


def initial_state(query: str, thread_id: str = "") -> AnalyserState:
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
        clarification_needed=False,
        clarification_message="",
        thread_id=thread_id,
        final_answer="",
    )