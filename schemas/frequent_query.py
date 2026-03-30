from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class IncomingQuery(BaseModel):
    query: str

class FrequentQuery(BaseModel):
    id: UUID
    canonical_query: str
    llm_response: str
    hit_count : int  
    last_asked_at: datetime 
    drug_names: list[str] 
    intent_category: str
    created_at: datetime

class CanonicalQuery(BaseModel):
    canonical_query: str
    drug_names: list[str] 
    intent_category: str