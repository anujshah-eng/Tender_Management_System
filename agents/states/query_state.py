#Agent/state/query_state.py
"""
State Definitions for Query Workflow
"""
from typing import TypedDict, List, Dict, Any, Literal


class AgentQueryState(TypedDict):
    """State for agent query workflow"""
    tender_file_id: int
    user_query: str
    agent_type: Literal["summary", "qa"]
    explanation_level: Literal["simple", "professional"]
    retrieved_chunks: List[Dict[str, Any]]
    response: str
    error: str
