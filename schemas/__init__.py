from pydantic import BaseModel
from .analyse_query import QueryRequest, QueryResponse


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str