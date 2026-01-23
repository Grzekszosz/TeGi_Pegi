from typing import List, Dict, Any
from neo4j import GraphDatabase
from langchain_core.tools import tool

from CVgetData.tools.assignment import assign_person_to_rfp
from CVgetData.tools.matching import list_rfps_with_skills, match_rfp
from .config import get_neo4j_config, init_neo4j

_neo4j_cfg = get_neo4j_config()
_driver = GraphDatabase.driver(
    _neo4j_cfg.uri, auth=(_neo4j_cfg.user, _neo4j_cfg.password)
)


@tool
def graph_cypher_query(description: str, cypher: str) -> List[Dict[str, Any]]:
    """
    Wykonuje zapytanie Cypher na grafie TalentMatch i zwraca wyniki jako listę słowników.

    Parametry:
    - description: krótki opis celu biznesowego zapytania (np. "Policz senior Java devów dostępnych w Q3 2025")
    - cypher: pełne zapytanie Cypher do wykonania.
    """
    with _driver.session() as session:
        result = session.run(cypher)
        records = [r.data() for r in result]
    return records


@tool
def tool_list_rfps() -> str:
    """List all RFPs with their skills."""
    g = init_neo4j()
    return str(list_rfps_with_skills(g))

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