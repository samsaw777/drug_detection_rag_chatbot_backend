from pydantic import BaseModel


class QueryRequest(BaseModel):
    raw_query: str


# Single interaction pair extracted by the analyser
class InteractionPair(BaseModel):
    type: str      
    drug: str
    target: str


# Normal Query Response
class QueryResponse(BaseModel):
    interactions: list[InteractionPair]
    clarification_needed: bool = False
    clarification_message: str = ""
    corrected_query: str = ""    
    final_output: str = ""


# Response sent to frontend when spelling or clarification is needed
class ClarificationResponse(BaseModel):
    type: str                      
    thread_id: str
    message: str
    corrections: list[dict] = []    