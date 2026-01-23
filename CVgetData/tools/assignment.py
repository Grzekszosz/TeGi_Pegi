from langchain_neo4j import Neo4jGraph

ASSIGN_QUERY = """
MATCH (p:Person {uuid:$person_uuid})
MATCH (r:RFP {id:$rfp_id})
MERGE (p)-[a:ASSIGNED_TO]->(r)
SET a.role = $role,
    a.allocation = $allocation,
    a.startDate = date($start_date),
    a.endDate   = date($end_date),
    a.updatedAt = datetime()
RETURN
  coalesce(p.full_name, p.uuid) AS person,
  p.uuid AS person_uuid,
  coalesce(r.title, r.id) AS rfp,
  a.role AS role,
  a.allocation AS allocation,
  toString(a.startDate) AS startDate,
  toString(a.endDate) AS endDate
"""

def assign_person_to_rfp(
    graph: Neo4jGraph,
    person_id: str,
    rfp_id: str,
    role: str,
    allocation: float,
    start_date: str,
    end_date: str,
):
    # minimalne walidacje po stronie Pythona
    if not (0 < allocation <= 1.0):
        raise ValueError("allocation must be in (0,1]")

    return graph.query(ASSIGN_QUERY, {
        "person_id": person_id,
        "rfp_id": rfp_id,
        "role": role,
        "allocation": allocation,
        "start_date": start_date,
        "end_date": end_date,
    })