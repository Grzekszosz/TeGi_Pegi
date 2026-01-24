from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from .config import init_neo4j
from .state import RouterState
from .nodes import classify_query, call_tools_and_answer
from langchain_core.tools import tool
from CVgetData.tools.matching import list_rfps, match_rfp
from CVgetData.tools.assignment import assign_person_to_rfp

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

@tool
def tool_list_rfps() -> str:
    """List all RFPs with id, title, client."""
    g = init_neo4j()
    return str(list_rfps(g))

@tool
def tool_match_rfp(rfp_id: str, mode: str = "auto") -> str:
    """Match candidates to given RFP id. mode=auto/strict/soft."""
    g = init_neo4j()
    return str(match_rfp(g, rfp_id, mode))

@tool
def tool_assign_person(person_id: str, rfp_id: str, role: str, allocation: float, start_date: str, end_date: str) -> str:
    """Assign person to RFP with role, allocation and date range."""
    g = init_neo4j()
    return str(assign_person_to_rfp(g, person_id, rfp_id, role, allocation, start_date, end_date))