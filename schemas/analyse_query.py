from pydantic import BaseModel

class QueryRequest(BaseModel):
    raw_query: str                

# Normal Query Response
class QueryResponse(BaseModel):
    interaction_types: list[str]   
    drugs: list[str]               
    foods: list[str]              
    herbs: list[str]               
    corrected_query: str = ""     

# Confirmation query response
class ClarificationResponse(BaseModel):
    """Returned when a spelling correction is detected and needs user confirmation."""
    needs_clarification: bool = True
    thread_id: str
    message: str
    corrections: list[dict]