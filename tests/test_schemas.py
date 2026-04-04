import pytest
from schemas import QueryRequest, QueryResponse, FrequentQuery, CanonicalQuery
import uuid
from datetime import datetime, timezone

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

def test_canonical_query():
    """Tests that CanonicalQuery"""

    canonical = CanonicalQuery(
    canonical_query= "drug interaction: aspirin warfarin",
    drug_names= ["aspirin","garlic","lisinopril"],
    intent_category= "interaction"
    )

    assert canonical.canonical_query == "drug interaction: aspirin warfarin"
    assert canonical.drug_names == ["aspirin","garlic","lisinopril"]
    assert canonical.intent_category == "interaction"


def test_frequent_query():
    """Tests frequent query object"""
    freq_query= FrequentQuery(
    id= uuid.uuid4(),
    canonical_query= "drug interaction: aspirin warfarin",
    llm_response= "Is there anything else I can assist you with?",
    hit_count =1,  
    last_asked_at= datetime.now(),
    drug_names= ["aspirin","garlic","lisinopril"],
    intent_category= "interaction",
    created_at= datetime.now(timezone.utc)
    )

    print(freq_query)