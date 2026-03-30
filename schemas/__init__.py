from pydantic import BaseModel
from .analyse_query import QueryRequest, QueryResponse
from .frequent_query import FrequentQuery, CanonicalQuery

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str