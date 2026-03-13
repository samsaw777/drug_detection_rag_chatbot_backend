import uuid
from dataclasses import dataclass

from Agent_Graph.analyser_graph import build_graph
from Agents_State.Query_state import initial_state
from schemas.query_response import QueryResponse
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command



# ─────────────────────────────────────────────────────────────────────────────
# CLARIFICATION RETURN TYPE
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ClarificationNeeded:
    """
    Returned when the graph pauses at interrupt() waiting for user input.

    thread_id   : pass back to confirm() to resume the right graph instance
    message     : human-readable string to show the user
    corrections : list of { original, corrected, type } dicts
    """
    thread_id: str
    message: str
    corrections: list[dict]


# ─────────────────────────────────────────────────────────────────────────────
# AGENT
# ─────────────────────────────────────────────────────────────────────────────

class QueryAnalyserAgent:
    """
    Wrapper around the QueryAnalyser LangGraph with HITL pause/resume.

    The graph is compiled once on __init__ and reused for every call.

    Happy path (no corrections):
        agent = QueryAnalyserAgent()
        result = agent.analyse("Does warfarin interact with garlic?")
        # result → QueryResponse directly

    HITL path (correction detected):
        result = agent.analyse("Does asprin interact with garlic?")
        # result → ClarificationNeeded
        #   .message    = 'I noticed: "asprin" → "aspirin". Reply "yes" or correct name.'
        #   .thread_id  = "abc-123"

        # User confirms:
        final = agent.confirm("abc-123", "yes")
        # final → QueryResponse ✅

        # User provides a different name:
        final = agent.confirm("abc-123", "acetylsalicylic acid")
        # final → QueryResponse ✅ (restarted with new name)
    """

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self._graph = build_graph()

    def analyse(self, query: str, thread_id: str = "") -> QueryResponse | ClarificationNeeded:
        """
        Start a fresh analysis for a user query.

        Args:
            query     : raw user input
            thread_id : optional — auto-generated if not provided

        Returns:
            QueryResponse       → no corrections needed, analysis complete
            ClarificationNeeded → correction detected, graph paused
        """
        if not thread_id:
            thread_id = str(uuid.uuid4())

        state = initial_state(query=query, thread_id=thread_id)
        config = RunnableConfig(configurable={"thread_id": thread_id})
        result = self._graph.invoke(state, config=config)

        return self._handle_result(result, thread_id)

    def confirm(self, thread_id: str, user_reply: str) -> QueryResponse | ClarificationNeeded:
        """
        Resume a paused graph after the user replies to a clarification.

        Args:
            thread_id  : from the ClarificationNeeded / ClarificationResponse
            user_reply : "yes" to accept correction, or any new drug/food/herb name

        Returns:
            QueryResponse       → analysis complete
            ClarificationNeeded → another correction found (edge case)
        """
        config = RunnableConfig(configurable={"thread_id": thread_id})

        # Resume the paused graph — pass user reply as the interrupt return value
        result = self._graph.invoke(
            Command(resume=user_reply),
            config=config,
        )

        return self._handle_result(result, thread_id)

    def _handle_result(
        self, result: dict, thread_id: str
    ) -> QueryResponse | ClarificationNeeded:
        """
        Inspect the finished/paused graph result.
        LangGraph surfaces interrupt() output inside result["__interrupt__"].
        """
        # Graph paused at interrupt()
        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            return ClarificationNeeded(
                thread_id=thread_id,
                message=interrupt_data["message"],
                corrections=interrupt_data["corrections"],
            )

        # Graph completed — check for failures
        if result.get("query_response") is None:
            raise ValueError(
                f"QueryAnalyserAgent failed.\n"
                f"Status : {result.get('status')}\n"
                f"Error  : {result.get('error')}"
            )

        return result["query_response"]