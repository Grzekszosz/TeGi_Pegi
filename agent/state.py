from typing import Optional
from langgraph.graph import MessagesState

class RouterState(MessagesState):
    query_type: Optional[str] = None
