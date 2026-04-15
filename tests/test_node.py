"""Tests for all graph node functions."""
from Agent_Nodes.query_nodes import (
    validate_input,
    parse_response,
    check_corrections,
    apply_confirmation,
    build_agent_response,
)




class TestValidateInput:

    def test_valid_query(self, clean_state):
        result = validate_input(clean_state)
        assert result["status"] == "ok"
        assert result["error"] == ""

    def test_empty_string(self, empty_query_state):
        result = validate_input(empty_query_state)
        assert result["status"] == "invalid_input"
        assert "empty" in result["error"].lower()

    def test_whitespace_only(self, whitespace_query_state):
        result = validate_input(whitespace_query_state)
        assert result["status"] == "invalid_input"
        assert "empty" in result["error"].lower()

    def test_preserves_query(self, clean_state):
        original = clean_state["query"]
        result = validate_input(clean_state)
        assert result["query"] == original




class TestParseResponse:

    def test_valid_json(self, clean_state):
        clean_state["llm_output"] = '{"interactions": [], "clarification_needed": false}'
        result = parse_response(clean_state)
        assert result["status"] == "ok"
        assert result["parsed"] is not None
        assert result["parsed"]["interactions"] == []

    def test_json_with_markdown_fences(self, clean_state):
        clean_state["llm_output"] = '```json\n{"interactions": [], "clarification_needed": false}\n```'
        result = parse_response(clean_state)
        assert result["status"] == "ok"
        assert result["parsed"] is not None

    def test_invalid_json(self, clean_state):
        clean_state["llm_output"] = "not valid json at all"
        result = parse_response(clean_state)
        assert result["status"] == "error"
        assert result["parsed"] is None
        assert "JSON parse failed" in result["error"]

    def test_invalid_json_increments_retry(self, clean_state):
        clean_state["llm_output"] = "broken"
        clean_state["retry_count"] = 0
        result = parse_response(clean_state)
        assert result["retry_count"] == 1

    def test_empty_llm_output(self, clean_state):
        clean_state["llm_output"] = ""
        result = parse_response(clean_state)
        assert result["status"] == "error"




class TestCheckCorrections:

    def test_valid_query_no_issues(self, valid_parsed_state):
        result = check_corrections(valid_parsed_state)
        assert result["is_valid"] is True
        assert result["awaiting_confirmation"] is False
        assert result["clarification_needed"] is False
        assert result["corrections_found"] == []

    def test_invalid_query_rejects(self, invalid_query_parsed_state):
        result = check_corrections(invalid_query_parsed_state)
        assert result["is_valid"] is False
        assert result["status"] == "invalid_query"
        assert result["awaiting_confirmation"] is False
        assert result["clarification_needed"] is False
        assert "drug-food" in result["final_answer"]

    def test_clarification_needed(self, clarification_parsed_state):
        result = check_corrections(clarification_parsed_state)
        assert result["is_valid"] is True
        assert result["clarification_needed"] is True
        assert result["awaiting_confirmation"] is True
        assert result["corrections_found"] == []

    def test_spelling_detected(self, spelling_parsed_state):
        result = check_corrections(spelling_parsed_state)
        assert result["is_valid"] is True
        assert result["clarification_needed"] is False
        assert result["awaiting_confirmation"] is True
        assert len(result["corrections_found"]) == 1
        assert result["corrections_found"][0]["original"] == "asprin"
        assert result["corrections_found"][0]["corrected"] == "aspirin"

    def test_both_spelling_and_clarification(self, both_parsed_state):
        result = check_corrections(both_parsed_state)
        assert result["is_valid"] is True
        assert result["clarification_needed"] is True
        assert result["awaiting_confirmation"] is True
        assert len(result["corrections_found"]) == 1

    def test_invalid_query_sets_final_answer(self, invalid_query_parsed_state):
        result = check_corrections(invalid_query_parsed_state)
        assert result["final_answer"] != ""

    def test_invalid_query_empty_corrections(self, invalid_query_parsed_state):
        result = check_corrections(invalid_query_parsed_state)
        assert result["corrections_found"] == []




class TestApplyConfirmation:

    # -- Spelling: user confirms --
    def test_spelling_accept(self, awaiting_spelling_state):
        awaiting_spelling_state["user_confirmation"] = "yes"
        result = apply_confirmation(awaiting_spelling_state)
        assert result["status"] == "ok"
        interactions = result["parsed"]["interactions"] # type: ignore
        assert interactions[0]["drug"] == "aspirin"

    def test_spelling_accept_updates_corrected_query(self, awaiting_spelling_state):
        awaiting_spelling_state["user_confirmation"] = "yes"
        result = apply_confirmation(awaiting_spelling_state)
        assert "aspirin" in result["parsed"]["corrected_query"] # pyright: ignore[reportOptionalSubscript]
        assert "asprin" not in result["parsed"]["corrected_query"] # type: ignore

    # -- Spelling: user provides new name --
    def test_spelling_custom_name(self, awaiting_spelling_state):
        awaiting_spelling_state["user_confirmation"] = "ibuprofen"
        result = apply_confirmation(awaiting_spelling_state)
        assert result["status"] == "restart"
        assert "ibuprofen" in result["query"]

    def test_spelling_custom_resets_state(self, awaiting_spelling_state):
        awaiting_spelling_state["user_confirmation"] = "ibuprofen"
        result = apply_confirmation(awaiting_spelling_state)
        assert result["parsed"] is None
        assert result["llm_output"] == ""
        assert result["corrections_found"] == []
        assert result["retry_count"] == 0

    # -- Clarification: user provides info --
    def test_clarification_combines_query(self, awaiting_clarification_state):
        awaiting_clarification_state["user_confirmation"] = "grapefruit"
        result = apply_confirmation(awaiting_clarification_state)
        assert result["status"] == "restart"
        assert "warfarin" in result["query"]
        assert "grapefruit" in result["query"]

    def test_clarification_resets_state(self, awaiting_clarification_state):
        awaiting_clarification_state["user_confirmation"] = "grapefruit"
        result = apply_confirmation(awaiting_clarification_state)
        assert result["parsed"] is None
        assert result["llm_output"] == ""
        assert result["clarification_needed"] is False
        assert result["corrections_found"] == []




class TestBuildAgentResponse:

    def test_builds_valid_response(self, valid_parsed_state):
        result = build_agent_response(valid_parsed_state)
        qr = result["query_response"]
        assert qr is not None
        assert len(qr.interactions) == 1
        assert qr.interactions[0].type == "drug-food"
        assert qr.interactions[0].drug == "warfarin"
        assert qr.interactions[0].target == "grapefruit"
        assert result["status"] == "ok"

    def test_invalid_query_returns_empty_response(self, invalid_query_parsed_state):
        # Simulate check_corrections having set invalid_query
        invalid_query_parsed_state["status"] = "invalid_query"
        invalid_query_parsed_state["final_answer"] = "I can only help with drug interactions."
        result = build_agent_response(invalid_query_parsed_state)
        qr = result["query_response"]
        assert qr is not None
        assert len(qr.interactions) == 0
        assert result["status"] == "invalid_query"

    def test_empty_interactions(self, clarification_parsed_state):
        result = build_agent_response(clarification_parsed_state)
        qr = result["query_response"]
        assert qr is not None
        assert len(qr.interactions) == 0
        assert qr.clarification_needed is True

    def test_multiple_interactions(self, clean_state):
        clean_state["parsed"] = {
            "interactions": [
                {"type": "drug-food", "drug": "warfarin", "target": "grapefruit"},
                {"type": "drug-herb", "drug": "warfarin", "target": "garlic"},
            ],
            "clarification_needed": False,
            "clarification_message": "",
            "corrected_query": "warfarin with grapefruit and garlic",
        }
        clean_state["status"] = "ok"
        result = build_agent_response(clean_state)
        qr = result["query_response"]
        assert len(qr.interactions) == 2 # type: ignore
        assert qr.interactions[0].target == "grapefruit" # type: ignore
        assert qr.interactions[1].target == "garlic" # type: ignore