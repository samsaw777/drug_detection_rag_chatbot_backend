from fastapi import APIRouter, HTTPException
from schemas import QueryRequest, QueryResponse
from services.analyser import QueryAnalyser
import os

router = APIRouter()
analyser = QueryAnalyser(api_key=os.getenv("GOOGLE_API_KEY"))

@router.post("/analyse", response_model=QueryResponse)
def analyse_query(user_query: QueryRequest):
    try:
        return analyser.analyse(user_query.raw_query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))