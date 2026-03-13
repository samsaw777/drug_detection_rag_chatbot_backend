from pydantic import BaseModel


class QueryResponse(BaseModel):
    interaction_types: list[str]
    drugs: list[str]
    foods: list[str]
    herbs: list[str]
    corrected_query: str