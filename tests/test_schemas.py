import pytest
from schemas import QueryRequest, QueryResponse, FrequentQuery

def test_query_request_valid():
    """Tests that QueryRequest correctly stores a valid user query."""
    request = QueryRequest(raw_query="does aspirin interact with warfarin?")
    assert request.raw_query == "does aspirin interact with warfarin?"

def test_query_response_valid():
    """Tests that QueryResponse correctly stores all extracted fields
    including interaction types, drugs, foods, herbs, and corrected query."""
    response = QueryResponse(
        interaction_types=["drug-drug"],
        drugs=["aspirin", "warfarin"],
        foods=[],
        herbs=[],
        corrected_query="does aspirin interact with warfarin?"
    )
    assert response.interaction_types == ["drug-drug"]
    assert response.drugs == ["aspirin", "warfarin"]
    assert response.foods == []
    assert response.herbs == []

def test_frequent_query():
    """Tests that FrequentQuery"""