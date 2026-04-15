from fastapi import APIRouter

from config import get_settings
from schemas import HealthResponse
from config import get_settings
from Agents.basic_agent import Test_agent

settings = get_settings()

router = APIRouter()
settings = get_settings()


@router.get("/")
async def initial_response():
    """Basic health check endpoint."""
    return {
        "Status":"200",
        "Message":"Hi, from the initial server"
    }

@router.post("/response")
async def basic_agent():
    output = await Test_agent() # pyright: ignore[reportGeneralTypeIssues]
    return {
        "output": output
    }