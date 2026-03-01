from pydantic import BaseModel

class QueryRequest(BaseModel):
    raw_query: str                 # original user query

class QueryResponse(BaseModel):
    interaction_types: list[str]   # ["drug-drug", "drug-food", "drug-herb"]
    drugs: list[str]               # extracted drug names
    foods: list[str]               # extracted food items
    herbs: list[str]               # extracted herb names
    corrected_query: str = ""      # Corrected query