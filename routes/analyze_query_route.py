"""
routes/analyze_query_route.py — Query analyser endpoints with HITL support.

POST /analyse           →  Start a new analysis
POST /analyse/confirm   →  Resume after user confirms or corrects a spelling
"""

from typing import Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from schemas import QueryRequest
from schemas.query_response import QueryResponse
from schemas.analyse_query import ClarificationResponse
from Agents.query_analyser import QueryAnalyserAgent, ClarificationNeeded

router = APIRouter()
agent = QueryAnalyserAgent()


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST SCHEMA
# ─────────────────────────────────────────────────────────────────────────────

class ConfirmRequest(BaseModel):
    thread_id: str    # returned in ClarificationResponse — identifies the paused graph
    user_reply: str   # "yes" to confirm correction, or a new drug/food/herb name


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyse", response_model=Union[QueryResponse, ClarificationResponse])
def analyse_query(user_query: QueryRequest):
    """
    Start a new drug/food/herb interaction analysis.

    Returns QueryResponse if no corrections needed.
    Returns ClarificationResponse if a spelling correction was detected —
    frontend should display the message and call POST /analyse/confirm.
    """
    try:
        result = agent.analyse(user_query.raw_query)

        if isinstance(result, ClarificationNeeded):
            return ClarificationResponse(
                thread_id=result.thread_id,
                message=result.message,
                corrections=result.corrections,
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyse/confirm", response_model=Union[QueryResponse, ClarificationResponse])
def confirm_correction(body: ConfirmRequest):
    """
    Resume a paused analysis after the user replies to a correction.

    user_reply = "yes"           → confirms LLM correction, resumes graph
    user_reply = "<new name>"    → plugs new name into original query, restarts analysis
    """
    try:
        result = agent.confirm(
            thread_id=body.thread_id,
            user_reply=body.user_reply,
        )

        if isinstance(result, ClarificationNeeded):
            return ClarificationResponse(
                thread_id=result.thread_id,
                message=result.message,
                corrections=result.corrections,
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))