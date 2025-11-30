from typing import List, Dict, Any
from neo4j import GraphDatabase
from langchain_core.tools import tool
from .config import get_neo4j_config

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
