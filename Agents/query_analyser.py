import uuid
from dataclasses import dataclass

from Agent_Graph.analyser_graph import build_graph
from Agents_State.Query_state import initial_state
from schemas.analyse_query import QueryResponse
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
import json


@dataclass
class ClarificationNeeded:
    type: str              
    thread_id: str
    message: str
    corrections: list[dict]


class QueryAnalyserAgent:

    def __init__(self, graph):
        self._graph = graph

    @classmethod
    async def create(cls, model: str = "gemini-2.5-flash"):
        graph = await build_graph()
        return cls(graph)

    async def analyse(self, query: str, thread_id: str = "") -> tuple[QueryResponse | ClarificationNeeded, str]:
        if not thread_id:
            thread_id = str(uuid.uuid4())

        state = initial_state(query=query, thread_id=thread_id)
        config = RunnableConfig(configurable={"thread_id": thread_id})
        result = await self._graph.ainvoke(state, config=config)

        return self._handle_result(result, thread_id), thread_id

    async def confirm(self, thread_id: str, user_reply: str) -> QueryResponse | ClarificationNeeded:
        config = RunnableConfig(configurable={"thread_id": thread_id})
        result = await self._graph.ainvoke(
            Command(resume=user_reply),
            config=config,
        )
        return self._handle_result(result, thread_id)

    def _handle_result(self, result: dict, thread_id: str) -> QueryResponse | ClarificationNeeded:
        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            return ClarificationNeeded(
                type=interrupt_data.get("type", "spelling"),
                thread_id=thread_id,
                message=interrupt_data["message"],
                corrections=interrupt_data.get("corrections", []),
            )

        if result.get("query_response") is None:
            raise ValueError(
                f"QueryAnalyserAgent failed.\n"
                f"Status : {result.get('status')}\n"
                f"Error  : {result.get('error')}"
            )

        query_response = result["query_response"]
        # This is for the final output which we will comment out later.
        # query_response.final_output = result.get("final_answer", "")

        query_response.final_output = json.dumps(result.get("sql_results", []), default=str)

        return query_response

    async def cleanup_thread(self, thread_id: str):
        """Delete checkpoint data for a completed thread."""
        pool = self._graph.checkpointer.conn
        async with pool.connection() as conn:
            await conn.execute("DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,))
            await conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_id,))
            await conn.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,))
        print(f"Deleted all records for thread: {thread_id}")