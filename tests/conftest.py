import pytest # type: ignore
from Agents_State.Query_state import AnalyserState, initial_state
 
 
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
