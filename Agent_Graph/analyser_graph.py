# """
# Agent_Graph/analyser_graph.py — Builds and compiles the QueryAnalyser LangGraph
#                                  with Redis checkpointer for HITL pause/resume.

# Full graph flow:
#     validate_input
#         ↓ ok                          ↓ invalid_input
#     analyse_query                 handle_error → END
#         ↓
#     parse_response
#         ↓ ok        ↓ error & retry<2    ↓ retries exhausted
#     check_corrections  retry_analyse    handle_error → END
#         ↓ no corrections   ↓ (loops back to parse_response)
#         ↓                  corrections found
#     format_output ←    ask_user         ← PAUSES HERE (interrupt)
#         ↓                   ↓ (resumes when user replies)
#        END             apply_confirmation
#                             ↓ "yes"          ↓ new name
#                         format_output    analyse_query (full restart)
#                             ↓
#                            END
# """

# import os
# from dotenv import load_dotenv

# from langgraph.graph import StateGraph, END
# from utils.redis_client import get_checkpointer

# from Agents_State.Query_state import AnalyserState
# from Agent_Nodes.query_nodes import (
#     validate_input,
#     analyse_query,
#     parse_response,
#     retry_analyse,
#     check_corrections,
#     ask_user,
#     apply_confirmation,
#     format_output,
#     handle_error,
# )

# load_dotenv()
# # ─────────────────────────────────────────────────────────────────────────────
# # ROUTING FUNCTIONS
# # ─────────────────────────────────────────────────────────────────────────────

# def route_after_validate(state: AnalyserState) -> str:
#     return "analyse_query" if state["status"] == "ok" else "handle_error"


# def route_after_parse(state: AnalyserState) -> str:
#     if state["status"] == "ok":
#         return "check_corrections"
#     if state.get("retry_count", 0) < 2:
#         return "retry_analyse"
#     return "handle_error"


# def route_after_corrections(state: AnalyserState) -> str:
#     """Corrections found → ask user. No corrections → go straight to output."""
#     return "ask_user" if state["awaiting_confirmation"] else "format_output"


# def route_after_confirmation(state: AnalyserState) -> str:
#     """
#     User said "yes" → format_output (keep LLM corrections, resume).
#     User gave new name → analyse_query (restart with new name).
#     """
#     return "analyse_query" if state["status"] == "restart" else "format_output"


# # ─────────────────────────────────────────────────────────────────────────────
# # GRAPH BUILDER
# # ─────────────────────────────────────────────────────────────────────────────

# def build_graph():
#     """
#     Compile and return the QueryAnalyser LangGraph with Redis checkpointer.
#     Call once at startup — reuse the compiled graph for all requests.
#     """
#     graph = StateGraph(AnalyserState)

#     # Register nodes
#     graph.add_node("validate_input",     validate_input)
#     graph.add_node("analyse_query",      analyse_query)
#     graph.add_node("parse_response",     parse_response)
#     graph.add_node("retry_analyse",      retry_analyse)
#     graph.add_node("check_corrections",  check_corrections)
#     graph.add_node("ask_user",           ask_user)
#     graph.add_node("apply_confirmation", apply_confirmation)
#     graph.add_node("format_output",      format_output)
#     graph.add_node("handle_error",       handle_error)

#     # Entry point
#     graph.set_entry_point("validate_input")

#     # Edges
#     graph.add_conditional_edges(
#         "validate_input",
#         route_after_validate,
#         {"analyse_query": "analyse_query", "handle_error": "handle_error"},
#     )

#     graph.add_edge("analyse_query", "parse_response")

#     graph.add_conditional_edges(
#         "parse_response",
#         route_after_parse,
#         {
#             "check_corrections": "check_corrections",
#             "retry_analyse":     "retry_analyse",
#             "handle_error":      "handle_error",
#         },
#     )

#     graph.add_edge("retry_analyse", "parse_response")

#     graph.add_conditional_edges(
#         "check_corrections",
#         route_after_corrections,
#         {"ask_user": "ask_user", "format_output": "format_output"},
#     )

#     graph.add_edge("ask_user", "apply_confirmation")

#     graph.add_conditional_edges(
#         "apply_confirmation",
#         route_after_confirmation,
#         {"analyse_query": "analyse_query", "format_output": "format_output"},
#     )

#     graph.add_edge("format_output", END)
#     graph.add_edge("handle_error",  END)

#     checkpointer = get_checkpointer()
#     return graph.compile(checkpointer=checkpointer)

"""
Agent_Graph/analyser_graph.py — Builds and compiles the QueryAnalyser LangGraph
                                 with Postgres checkpointer for HITL pause/resume.
"""

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
    format_output,
    handle_error,
    frequent_query_check
)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTING FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def route_after_validate(state: AnalyserState) -> str:
    return "analyse_query" if state["status"] == "ok" else "handle_error"


def route_after_parse(state: AnalyserState) -> str:
    if state["status"] == "ok":
        return "check_corrections"
    if state.get("retry_count", 0) < 2:
        return "retry_analyse"
    return "handle_error"


def route_after_corrections(state: AnalyserState) -> str:
    return "ask_user" if state["awaiting_confirmation"] else "format_output"


def route_after_confirmation(state: AnalyserState) -> str:
    return "analyse_query" if state["status"] == "restart" else "format_output"


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH BUILDER
# ─────────────────────────────────────────────────────────────────────────────

async def build_graph():
    """
    Compile and return the QueryAnalyser LangGraph with Postgres checkpointer.
    Call once at startup — reuse the compiled graph for all requests.
    """
    graph = StateGraph(AnalyserState)

    graph.add_node("validate_input",     validate_input)
    # graph.add_node("frequent_query_check", frequent_query_check)
    graph.add_node("analyse_query",      analyse_query)
    graph.add_node("parse_response",     parse_response)
    graph.add_node("retry_analyse",      retry_analyse)
    graph.add_node("check_corrections",  check_corrections)
    graph.add_node("ask_user",           ask_user)
    graph.add_node("apply_confirmation", apply_confirmation)
    graph.add_node("format_output",      format_output)
    graph.add_node("handle_error",       handle_error)

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
        {"ask_user": "ask_user", "format_output": "format_output"},
    )
    graph.add_edge("ask_user", "apply_confirmation")
    graph.add_conditional_edges(
        "apply_confirmation",
        route_after_confirmation,
        {"analyse_query": "analyse_query", "format_output": "format_output"},
    )
    graph.add_edge("format_output", END)
    graph.add_edge("handle_error",  END)

    checkpointer = await get_checkpointer()
    return graph.compile(checkpointer=checkpointer)