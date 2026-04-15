import pytest
from Agents_State.Query_state import AnalyserState, initial_state


# ── Basic query states ──

@pytest.fixture
def clean_state() -> AnalyserState:
    """A fresh state with a valid drug interaction query."""
    return initial_state(query="Does warfarin interact with garlic?")


@pytest.fixture
def empty_query_state() -> AnalyserState:
    return initial_state(query="")


@pytest.fixture
def whitespace_query_state() -> AnalyserState:
    return initial_state(query="      ")


@pytest.fixture
def valid_parsed_state() -> AnalyserState:
    """State after a successful LLM parse — complete interaction pair, no issues."""
    state = initial_state(query="Does warfarin interact with grapefruit?")
    state["parsed"] = {
        "is_valid": True,
        "interactions": [
            {"type": "drug-food", "drug": "warfarin", "target": "grapefruit"}
        ],
        "clarification_needed": False,
        "clarification_message": "",
        "corrected_query": "Does warfarin interact with grapefruit?",
        "spelling_flags": [],
    }
    state["status"] = "ok"
    return state


@pytest.fixture
def invalid_query_parsed_state() -> AnalyserState:
    """State after analyser rejects a gibberish query."""
    state = initial_state(query="Hello")
    state["parsed"] = {
        "is_valid": False,
        "interactions": [],
        "clarification_needed": False,
        "clarification_message": "I can only help with drug-food, drug-herb, or drug-drug interactions. Please ask a question that includes specific drug, food, or herb names.",
        "corrected_query": "Hello",
        "spelling_flags": [],
    }
    state["status"] = "ok"
    return state


@pytest.fixture
def clarification_parsed_state() -> AnalyserState:
    """State after analyser detects an incomplete query needing clarification."""
    state = initial_state(query="What interacts with warfarin?")
    state["parsed"] = {
        "is_valid": True,
        "interactions": [],
        "clarification_needed": True,
        "clarification_message": "Are you looking for food, herb, or drug interactions with warfarin?",
        "corrected_query": "What interacts with warfarin?",
        "spelling_flags": [],
    }
    state["status"] = "ok"
    return state


@pytest.fixture
def spelling_parsed_state() -> AnalyserState:
    """State after analyser detects a spelling issue in a complete query."""
    state = initial_state(query="Does asprin interact with grapefruit?")
    state["parsed"] = {
        "is_valid": True,
        "interactions": [
            {"type": "drug-food", "drug": "asprin", "target": "grapefruit"}
        ],
        "clarification_needed": False,
        "clarification_message": "",
        "corrected_query": "Does asprin interact with grapefruit?",
        "spelling_flags": [
            {"original": "asprin", "suggested": "aspirin", "type": "drug"}
        ],
    }
    state["status"] = "ok"
    return state


@pytest.fixture
def both_parsed_state() -> AnalyserState:
    """State after analyser detects both spelling issues and missing information."""
    state = initial_state(query="Does asprin interact with food?")
    state["parsed"] = {
        "is_valid": True,
        "interactions": [],
        "clarification_needed": True,
        "clarification_message": "Please specify which food you'd like to check with aspirin.",
        "spelling_flags": [
            {"original": "asprin", "suggested": "aspirin", "type": "drug"}
        ],
    }
    state["status"] = "ok"
    return state



@pytest.fixture
def awaiting_spelling_state() -> AnalyserState:
    """State paused at HITL for spelling correction."""
    state = initial_state(query="Does asprin interact with grapefruit?")
    state["parsed"] = {
        "is_valid": True,
        "interactions": [
            {"type": "drug-food", "drug": "asprin", "target": "grapefruit"}
        ],
        "clarification_needed": False,
        "clarification_message": "",
        "corrected_query": "Does asprin interact with grapefruit?",
        "spelling_flags": [],
    }
    state["corrections_found"] = [
        {"original": "asprin", "corrected": "aspirin", "type": "drug"}
    ]
    state["clarification_needed"] = False
    state["awaiting_confirmation"] = False
    return state


@pytest.fixture
def awaiting_clarification_state() -> AnalyserState:
    """State paused at HITL for clarification."""
    state = initial_state(query="What interacts with warfarin?")
    state["clarification_needed"] = True
    state["clarification_message"] = "Are you looking for food, herb, or drug interactions?"
    state["corrections_found"] = []
    state["awaiting_confirmation"] = False
    return state