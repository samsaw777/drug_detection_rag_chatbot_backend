from Agent_Nodes.query_nodes import validate_input



def test_validate_input_valid_query(clean_state):
    """Valid query should pass — status 'ok', no error."""
    result = validate_input(clean_state)
    assert result["status"] == "ok"
    assert result["error"] == ""


def test_validate_input_empty_string(empty_query_state):
    """Empty string should be rejected with 'invalid_input' status."""
    result = validate_input(empty_query_state)
    assert result["status"] == "invalid_input"
    assert "empty" in result["error"].lower()
 
 
def test_validate_input_whitespace_only(whitespace_query_state):
    """Whitespace-only string should be rejected just like empty."""
    result = validate_input(whitespace_query_state)
    assert result["status"] == "invalid_input"
    assert "empty" in result["error"].lower()
 
 
def test_validate_input_preserves_query(clean_state):
    """validate_input should never modify the original query."""
    original_query = clean_state["query"]
    result = validate_input(clean_state)
    assert result["query"] == original_query
