from fastapi import APIRouter

from .health import router as health_router
from .main_route import router as main_router
from .analyze_query_route import router as query_router


main_route = APIRouter()
main_route.include_router(main_router, tags=["main_router"])


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(query_router, tags=["Query"])


__all__ = ["api_router","main_route"]