from typing import Optional
from langgraph.graph import MessagesState

class RouterState(MessagesState):
    # dodatkowe pole na typ zapytania (counting / filtering / ...)
    query_type: Optional[str] = None
