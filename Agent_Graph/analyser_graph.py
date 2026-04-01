from langgraph.graph import StateGraph, END
from utils.db_checkpoint import get_checkpointer

from Agents_State.Query_state import AnalyserState
from Agent_Nodes.query_nodes import (
    validate_input,
    analyse_query,
    parse_response,
    retry_analyse,
    check_corrections,
    ask_user,
    apply_confirmation,
    build_agent_response,
    format_output,
    handle_error,
    fetch_data
)



def route_after_validate(state: AnalyserState) -> str:
    return "analyse_query" if state["status"] == "ok" else "handle_error"


def route_after_parse(state: AnalyserState) -> str:
    if state["status"] == "ok":
        return "check_corrections"
    if state.get("retry_count", 0) < 2:
        return "retry_analyse"
    return "handle_error"


def route_after_corrections(state: AnalyserState) -> str:
    return "ask_user" if state["awaiting_confirmation"] else "build_query_response"


def route_after_confirmation(state: AnalyserState) -> str:
    return "analyse_query" if state["status"] == "restart" else "build_query_response"

# Graph builder
async def build_graph():
    """
    Compile and return the QueryAnalyser LangGraph with Postgres checkpointer.
    Call once at startup — reuse the compiled graph for all requests.
    """
    graph = StateGraph(AnalyserState)

    graph.add_node("validate_input",       validate_input)
    graph.add_node("analyse_query",        analyse_query)
    graph.add_node("parse_response",       parse_response)
    graph.add_node("retry_analyse",        retry_analyse)
    graph.add_node("check_corrections",    check_corrections)
    graph.add_node("ask_user",             ask_user)
    graph.add_node("apply_confirmation",   apply_confirmation)
    graph.add_node("build_query_response", build_agent_response)
    graph.add_node("format_output",        format_output)
    graph.add_node("handle_error",         handle_error)
    graph.add_node("fetch_data",            fetch_data)


    graph.set_entry_point("validate_input")

    graph.add_conditional_edges(
        "validate_input",
        route_after_validate,
        {"analyse_query": "analyse_query", "handle_error": "handle_error"},
    )
    graph.add_edge("analyse_query", "parse_response")
    graph.add_conditional_edges(
        "parse_response",
        route_after_parse,
        {
            "check_corrections": "check_corrections",
            "retry_analyse":     "retry_analyse",
            "handle_error":      "handle_error",
        },
    )
    graph.add_edge("retry_analyse", "parse_response")
    graph.add_conditional_edges(
        "check_corrections",
        route_after_corrections,
        {"ask_user": "ask_user", "build_query_response": "build_query_response"},
    )
    graph.add_edge("ask_user", "apply_confirmation")
    graph.add_conditional_edges(
        "apply_confirmation",
        route_after_confirmation,
        {"analyse_query": "analyse_query", "build_query_response": "build_query_response"},
    )
    # graph.add_edge("build_query_response", "format_output")
    graph.add_edge("build_query_response", "fetch_data")
    graph.add_edge("fetch_data","format_output")
    graph.add_edge("format_output", END)
    # graph.add_edge("fetch_data", END)
    graph.add_edge("handle_error",  END)

    checkpointer = await get_checkpointer()
    return graph.compile(checkpointer=checkpointer)
