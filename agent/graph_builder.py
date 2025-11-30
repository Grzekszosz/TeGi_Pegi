from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from .state import RouterState
from .nodes import classify_query, call_tools_and_answer

def build_graph():
    workflow = StateGraph(RouterState)

    workflow.add_node("router", classify_query)
    workflow.add_node("agent", call_tools_and_answer)

    workflow.add_edge(START, "router")
    workflow.add_edge("router", "agent")
    workflow.add_edge("agent", END)

    graph = workflow.compile()
    return graph

graph = build_graph()

def run_business_query(user_text: str) -> str:
    initial_state = {
        "messages": [HumanMessage(content=user_text)]
    }
    final_state = graph.invoke(initial_state)
    return final_state["messages"][-1].content

