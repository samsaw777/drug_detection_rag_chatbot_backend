from fastapi import APIRouter

from config import get_settings
from schemas import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get("/")
async def initial_response():
    """Basic health check endpoint."""
    return {
        "Status":"200",
        "Message":"Hi, from the initial server"
    }