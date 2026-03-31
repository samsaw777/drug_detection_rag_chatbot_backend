from typing import Union
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from schemas import QueryRequest
from schemas.analyse_query import QueryResponse
from schemas.analyse_query import ClarificationResponse
from Agents.query_analyser import ClarificationNeeded

router = APIRouter()


class ConfirmRequest(BaseModel):
    thread_id: str
    user_reply: str


@router.post("/analyse", response_model=Union[QueryResponse, ClarificationResponse])
async def analyse_query(user_query: QueryRequest, request: Request):
    try:
        agent = request.app.state.agent
        result, thread_id = await agent.analyse(user_query.raw_query)

        if isinstance(result, ClarificationNeeded):
            return ClarificationResponse(
                type=result.type,
                thread_id=result.thread_id,
                message=result.message,
                corrections=result.corrections,
            )

        # Graph completed — clean up checkpoints
        await agent.cleanup_thread(thread_id)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyse/confirm", response_model=Union[QueryResponse, ClarificationResponse])
async def confirm_correction(body: ConfirmRequest, request: Request):
    try:
        agent = request.app.state.agent
        result = await agent.confirm(
            thread_id=body.thread_id,
            user_reply=body.user_reply,
        )

        if isinstance(result, ClarificationNeeded):
            return ClarificationResponse(
                type=result.type,
                thread_id=result.thread_id,
                message=result.message,
                corrections=result.corrections,
            )

        # Graph completed — clean up checkpoints
        await agent.cleanup_thread(body.thread_id)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))