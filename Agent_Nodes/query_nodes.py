"""
Agent_Nodes/nodes.py — All LangGraph node functions for the QueryAnalyser agent.

Nodes:
    validate_input      →  Reject empty queries before wasting an LLM call
    analyse_query       →  Send query to Gemini, get raw JSON string back
    parse_response      →  Parse raw string into a Python dict
    retry_analyse       →  Re-prompt LLM with bad output so it can self-correct
    check_corrections   →  Read spelling_flags from parsed LLM output
    ask_user            →  Pause graph via interrupt(), surface message to user
    apply_confirmation  →  Apply "yes" (resume) or new name (restart)
    format_output       →  Convert parsed dict → typed QueryResponse
    handle_error        →  Terminal failure node
"""

import json
import re

from langgraph.types import interrupt

from Agents_State.Query_state import AnalyserState
from config.llm import get_llm
from Agent_Prompts.analyser_prompt import ANALYSER_PROMPT, RETRY_PROMPT_TEMPLATE
from services.fetch_query import FrequentFetcherCapture

from config import get_settings

settings= get_settings()
fetcher= FrequentFetcherCapture(api_key= settings.GEMINI_API_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _extract_text(response) -> str:
    """Safely extract plain string from Gemini response (content can be list or str)."""
    if isinstance(response.content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in response.content
        ).strip()
    return str(response.content).strip()


def _strip_fences(raw: str) -> str:
    """Remove markdown code fences Gemini sometimes wraps JSON in."""
    return re.sub(r"```(?:json|JSON)?\s*", "", raw).replace("```", "").strip()


# ─────────────────────────────────────────────────────────────────────────────
# NODES
# ─────────────────────────────────────────────────────────────────────────────

def validate_input(state: AnalyserState) -> AnalyserState:
    """Node 1 — Guard rail. Rejects empty or whitespace-only queries."""
    if not state["query"] or not state["query"].strip():
        return {**state, "status": "invalid_input", "error": "Query cannot be empty."}
    return {**state, "status": "ok", "error": ""}


async def frequent_query_check(state: AnalyserState) -> AnalyserState:
    """Check if the input query is frequently asked"""
    canonical_data = await fetcher.canonicalize(state['query'])

    if canonical_data.canonical_query =="NIL":
        return {**state, "is_frequent_fetched":False, "canonical_query":None, "frequent_response":None}
    frequent_response = fetcher.check_frequent_prompts(state["query"])

    return {**state, "is_frequent_fetched":frequent_response is not None, 
            "canonical_query":canonical_data, "frequent_response":frequent_response}


def analyse_query(state: AnalyserState) -> AnalyserState:
    """Node 2 — LLM call. Sends query to Gemini and stores raw response."""
    llm = get_llm()
    formatted_prompt = ANALYSER_PROMPT.format(query=state["query"])
    response = llm.invoke(formatted_prompt)
    raw = _extract_text(response)
    return {**state, "llm_output": raw, "status": "ok", "error": ""}


def parse_response(state: AnalyserState) -> AnalyserState:
    """Node 3 — JSON parser. Strips fences then parses LLM output into a dict."""
    raw = _strip_fences(state["llm_output"])
    try:
        parsed = json.loads(raw)
        return {**state, "parsed": parsed, "status": "ok", "error": ""}
    except json.JSONDecodeError as e:
        return {
            **state,
            "parsed": None,
            "status": "error",
            "error": f"JSON parse failed: {e} | Raw: {raw[:200]}",
            "retry_count": state.get("retry_count", 0) + 1,
        }


def retry_analyse(state: AnalyserState) -> AnalyserState:
    """Node 4 — Self-correction. Re-calls LLM with the broken output injected."""
    llm = get_llm()
    retry_prompt = RETRY_PROMPT_TEMPLATE.format(
        bad_output=state["llm_output"],
        query=state["query"],
    )
    response = llm.invoke(retry_prompt)
    raw = _extract_text(response)
    return {**state, "llm_output": raw, "status": "ok", "error": ""}


def check_corrections(state: AnalyserState) -> AnalyserState:
    """
    Node 5 — HITL gate.
    Reads spelling_flags directly from the LLM's parsed output.
    The LLM now flags misspellings explicitly instead of silently correcting them,
    so no heuristic comparison needed — just read what the LLM flagged.

    If spelling_flags is non-empty → set awaiting_confirmation=True so router
    sends to ask_user. Otherwise → continue straight to format_output.
    """
    spelling_flags = (state["parsed"] or {}).get("spelling_flags", [])

    corrections = [
        {
            "original": flag["original"],
            "corrected": flag["suggested"],
            "type": flag["type"],
        }
        for flag in spelling_flags
    ]

    return {
        **state,
        "corrections_found": corrections,
        "awaiting_confirmation": len(corrections) > 0,
    }


def ask_user(state: AnalyserState) -> AnalyserState:
    """
    Node 6 — Interrupt point.
    Pauses the graph and surfaces a clarification message to the caller.
    LangGraph saves the full AnalyserState to Redis via the checkpointer.

    interrupt() behaviour:
    - Freezes graph execution at this node
    - Returns the passed value as the graph's current output
    - Graph resumes when .invoke() is called again with the same thread_id
    """
    corrections = state["corrections_found"]
    suggestions = ", ".join(
        f'"{c["original"]}" → did you mean "{c["corrected"]}"?'
        for c in corrections
    )
    message = (
        f"I noticed some possible spelling issues: {suggestions} "
        f'Reply "yes" to confirm, or provide the correct name(s).'
    )

    # Pauses graph — user_reply is populated when graph resumes
    user_reply = interrupt({"message": message, "corrections": corrections})

    return {**state, "user_confirmation": user_reply, "awaiting_confirmation": False}


def apply_confirmation(state: AnalyserState) -> AnalyserState:
    """
    Node 7 — Apply user reply after resuming from interrupt.

    Two cases:
    - User said "yes"      → accept LLM's suggested corrections, continue to format_output
    - User gave a new name → plug it into the original query, restart full analysis
    """
    user_reply = state["user_confirmation"].strip().lower()
    corrections = state["corrections_found"]

    if user_reply == "yes":
        # User confirmed — replace original misspelled names with LLM suggestions in parsed
        parsed = dict(state["parsed"] or {})

        for correction in corrections:
            original = correction["original"]
            corrected = correction["corrected"]
            item_type = correction["type"]

            # Swap the misspelled name for the corrected one in the parsed dict
            key = item_type + "s"  # "drug" → "drugs", "food" → "foods", "herb" → "herbs"
            if key in parsed:
                parsed[key] = [
                    corrected if item.lower() == original.lower() else item
                    for item in parsed[key]
                ]

        # Also update corrected_query with confirmed corrections
        corrected_query = state["query"]
        for correction in corrections:
            corrected_query = re.sub(
                rf'\b{re.escape(correction["original"])}\b',
                correction["corrected"],
                corrected_query,
                flags=re.IGNORECASE,
            )
        parsed["corrected_query"] = corrected_query

        return {**state, "parsed": parsed, "status": "ok"}

    # User provided a new name — plug it into original query and restart
    new_query = state["query"]
    for correction in corrections:
        new_query = re.sub(
            rf'\b{re.escape(correction["original"])}\b',
            user_reply,
            new_query,
            flags=re.IGNORECASE,
        )

    return {
        **state,
        "query": new_query,
        "llm_output": "",
        "parsed": None,
        "corrections_found": [],
        "user_confirmation": "",
        "retry_count": 0,
        "status": "restart",
    }


def format_output(state: AnalyserState) -> AnalyserState:
    """Node 8 — Converts parsed dict into a typed QueryResponse Pydantic model."""
    from schemas.query_response import QueryResponse

    p = state["parsed"] or {}
    response = QueryResponse(
        interaction_types=p.get("interaction_types", []),
        drugs=p.get("drugs", []),
        foods=p.get("foods", []),
        herbs=p.get("herbs", []),
        corrected_query=p.get("corrected_query", state["query"]),
    )
    return {**state, "query_response": response, "status": "ok"}


def handle_error(state: AnalyserState) -> AnalyserState:
    """Terminal error node. Sets query_response to None so callers detect failure."""
    return {**state, "query_response": None}