"""Tests for Pydantic schema validation."""
import pytest
from schemas import QueryRequest
from schemas.analyse_query import (
    QueryResponse,
    InteractionPair,
    ClarificationResponse,
)




class TestQueryRequest:

    def test_valid_query(self):
        request = QueryRequest(raw_query="Does aspirin interact with warfarin?")
        assert request.raw_query == "Does aspirin interact with warfarin?"

    def test_empty_query(self):
        request = QueryRequest(raw_query="")
        assert request.raw_query == ""



class TestInteractionPair:

    def test_drug_food(self):
        pair = InteractionPair(type="drug-food", drug="warfarin", target="grapefruit")
        assert pair.type == "drug-food"
        assert pair.drug == "warfarin"
        assert pair.target == "grapefruit"

    def test_drug_herb(self):
        pair = InteractionPair(type="drug-herb", drug="warfarin", target="garlic")
        assert pair.type == "drug-herb"

    def test_drug_drug(self):
        pair = InteractionPair(type="drug-drug", drug="aspirin", target="warfarin")
        assert pair.type == "drug-drug"




class TestQueryResponse:

    def test_valid_response_with_interactions(self):
        response = QueryResponse(
            interactions=[
                InteractionPair(type="drug-food", drug="warfarin", target="grapefruit")
            ],
            clarification_needed=False,
            clarification_message="",
            corrected_query="Does warfarin interact with grapefruit?",
        )
        assert len(response.interactions) == 1
        assert response.interactions[0].drug == "warfarin"
        assert response.clarification_needed is False

    def test_empty_interactions(self):
        response = QueryResponse(
            interactions=[],
            clarification_needed=True,
            clarification_message="Which food are you asking about?",
            corrected_query="Does warfarin interact with food?",
        )
        assert len(response.interactions) == 0
        assert response.clarification_needed is True
        assert response.clarification_message != ""

    def test_multiple_interactions(self):
        response = QueryResponse(
            interactions=[
                InteractionPair(type="drug-food", drug="warfarin", target="grapefruit"),
                InteractionPair(type="drug-herb", drug="warfarin", target="garlic"),
            ],
            corrected_query="warfarin with grapefruit and garlic",
        )
        assert len(response.interactions) == 2

    def test_defaults(self):
        response = QueryResponse(
            interactions=[],
            corrected_query="test",
        )
        assert response.clarification_needed is False
        assert response.clarification_message == ""



class TestClarificationResponse:

    def test_spelling_response(self):
        response = ClarificationResponse(
            type="spelling",
            thread_id="abc-123",
            message='Did you mean "aspirin"?',
            corrections=[
                {"original": "asprin", "corrected": "aspirin", "type": "drug"}
            ],
        )
        assert response.type == "spelling"
        assert response.thread_id == "abc-123"
        assert len(response.corrections) == 1

    def test_clarification_response(self):
        response = ClarificationResponse(
            type="clarification",
            thread_id="abc-123",
            message="Which food are you asking about?",
            corrections=[],
        )
        assert response.type == "clarification"
        assert response.corrections == []

    def test_both_response(self):
        response = ClarificationResponse(
            type="both",
            thread_id="abc-123",
            message="Spelling issue and missing info.",
            corrections=[
                {"original": "asprin", "corrected": "aspirin", "type": "drug"}
            ],
        )
        assert response.type == "both"
        assert len(response.corrections) == 1