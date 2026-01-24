from typing import List, Dict, Any
from neo4j import GraphDatabase
from langchain_core.tools import tool

from CVgetData.tools.analitics import avg_project_duration, find_available_persons, pipeline_skill_gaps
from CVgetData.tools.assignment import assign_person_to_rfp, list_assigned_people, list_project_assignments_to_rfp, \
    explain_match
from CVgetData.tools.matching import list_rfps_with_skills, match_rfp
from CVgetData.tools.persons import list_persons, get_person_graph, search_persons, list_unassigned_persons, \
    find_persons_by_skills
from .config import get_neo4j_config, init_neo4j

_neo4j_cfg = get_neo4j_config()
_driver = GraphDatabase.driver(
    _neo4j_cfg.uri, auth=(_neo4j_cfg.user, _neo4j_cfg.password)
)

#deprecated
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

#Dopasuj mi Person do RFP "Enterprise Web Application Development" soft
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

@tool
def tool_list_persons(limit: int = 50) -> str:
    """List people with uuid, name and skills."""
    g = init_neo4j()
    return str(list_persons(g, limit))

@tool
def tool_get_person_graph(uuid: str) -> str:
    """Get details of a person by uuid (name, email, skills)."""
    g = init_neo4j()
    return str(get_person_graph(g, uuid))

@tool
def tool_search_person(fullname:str) ->str:
    """Search person by fullname."""
    g = init_neo4j()
    return str(search_persons(g, fullname))

@tool
def tool_list_assigned_people(rfp_id: str) -> str:
    """List people assigned to a given RFP (ASSIGNED_TO) with role/allocation/dates."""
    g = init_neo4j()
    return str(list_assigned_people(g, rfp_id))

#Pokaż mi Person nie przypisanych do żadnego RFP
@tool
def tool_list_unassigned_persons() -> str:
    """List all persons that are not assigned to any RFP project."""
    g = init_neo4j()
    return str(list_unassigned_persons(g))

#Pokaż mi Person przypisane do RFP API Integration Platform Development (dla MedTech Industries)
@tool
def tool_list_persons_not_in_rfp(rfp_id: str) -> str:
    """List persons not assigned to a specific RFP (they may be assigned elsewhere)."""
    g = init_neo4j()
    return str(list_project_assignments_to_rfp(g,rfp_id))

#Pokaż mi Person z umiejętnościami Python oraz Kubernetes
@tool
def tool_find_persons_by_skills(skills: list[str], mode: str = "all") -> str:
    """
    Find persons by skills.
    mode='all' -> must have all skills (AND)
    mode='any' -> any of skills (OR)
    """
    g = init_neo4j()
    return str(find_persons_by_skills(g, skills, mode))

#Pokaż mi średni czas trwania RFP
@tool
def tool_avg_project_duration() -> str:
    """Return average project duration based on RFP.duration_months (plus min/max/median)."""
    g = init_neo4j()
    return str(avg_project_duration(g))

#Pokaż mi dostępne osoby od 2025-10-01
@tool
def tool_find_available_persons(
    start_date: str,
    end_date: str,
    min_available: float = 1.0,
) -> str:
    """
    Find persons with available capacity in a given time window.

    Availability is calculated as:
    available = 1.0 - sum(allocation of overlapping assignments)

    Parameters:
    - start_date: window start (YYYY-MM-DD)
    - end_date: window end (YYYY-MM-DD)
    - min_available: minimum required availability (e.g. 0.5, 1.0)
    """
    g = init_neo4j()
    return str(
        find_available_persons(g, start_date, end_date, min_available)
    )

#Jakie mamy największe braki w projektach startujących w 2025?
@tool
def tool_pipeline_skill_gaps(from_date: str, to_date: str, limit: int = 50) -> str:
    """
    Skills gaps analysis for upcoming project pipeline.

    Looks at RFPs with start_date in [from_date, to_date],
    aggregates required skills (NEEDS) and compares them with supply
    (# of persons having HAS_SKILL for that skill).

    Returns gaps for mandatory and total requirements.
    Dates format: YYYY-MM-DD
    """
    g = init_neo4j()
    return str(pipeline_skill_gaps(g, from_date, to_date, limit))

#Wyjaśnij czemu dopsowujesz osoby do RFP "Enterprise Web Application Development"
@tool
def tool_explain_match(rfp_id: str, person_uuid: str) -> str:
    """
    Explain why a given person matches (or not) a given RFP.
    Returns matched/missing skills, mandatory pass/fail, match percent,
    and availability in the project time window.
    """
    g = init_neo4j()
    return str(explain_match(g, rfp_id, person_uuid))