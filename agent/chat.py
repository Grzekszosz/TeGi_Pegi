from langchain_core.messages import HumanMessage, AIMessage

from agent.graph_builder import build_graph

_graph = None  # singleton

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph

def run_chat(history: list[dict]) -> str:
    graph = get_graph()

    messages = []
    for m in history:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        else:
            messages.append(AIMessage(content=m["content"]))

    final_state = graph.invoke({"messages": messages})
    return final_state["messages"][-1].content
