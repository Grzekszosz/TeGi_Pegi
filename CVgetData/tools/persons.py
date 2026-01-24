from langchain_neo4j import Neo4jGraph
LIST_PERSONS = """
MATCH (p:Person)
OPTIONAL MATCH (p)-[:HAS_SKILL]->(s:Skill)
WITH p, collect(DISTINCT s.name) AS skills
RETURN
  p.uuid AS uuid,
  coalesce(p.full_name, trim(coalesce(p.first_name,'') + ' ' + coalesce(p.last_name,'')), p.uuid) AS name,
  skills
ORDER BY name
LIMIT $limit;
"""

def list_persons(graph: Neo4jGraph, limit: int = 50):
    return graph.query(LIST_PERSONS, {"limit": limit})

from langchain_neo4j import Neo4jGraph

GET_PERSON_GRAPH = """
MATCH (p:Person {uuid:$uuid})
CALL {
  WITH p
  MATCH (p)-[r]->(n)
  RETURN 'out' AS dir, type(r) AS rel_type, labels(n) AS labels,
         coalesce(n.name, n.title, n.full_name, n.id, n.uuid, '(no-label)') AS node,
         properties(r) AS rel_props
  UNION
  WITH p
  MATCH (n)-[r]->(p)
  RETURN 'in' AS dir, type(r) AS rel_type, labels(n) AS labels,
         coalesce(n.name, n.title, n.full_name, n.id, n.uuid, '(no-label)') AS node,
         properties(r) AS rel_props
}
RETURN dir, rel_type, labels, node, rel_props
ORDER BY dir, rel_type, node
"""

def get_person_graph(graph: Neo4jGraph, uuid: str):
    rows = graph.query(GET_PERSON_GRAPH, {"uuid": uuid})
    return rows


SEARCH_PERSONS = """
MATCH (p:Person)
WHERE toLower(coalesce(p.full_name,'')) CONTAINS toLower($q)
   OR toLower(coalesce(p.first_name,'')) CONTAINS toLower($q)
   OR toLower(coalesce(p.last_name,'')) CONTAINS toLower($q)
RETURN
  p.uuid AS uuid,
  coalesce(p.full_name, trim(coalesce(p.first_name,'') + ' ' + coalesce(p.last_name,'')), p.uuid) AS name
ORDER BY name
LIMIT 10;
"""

def search_persons(graph: Neo4jGraph, q: str):
    return graph.query(SEARCH_PERSONS, {"q": q})

LIST_UNASSIGNED_PERSONS = """
MATCH (p:Person)
WHERE NOT (p)-[:ASSIGNED_TO]->(:RFP)
RETURN
  p.uuid AS person_uuid,
  coalesce(p.full_name, trim(coalesce(p.first_name,'') + ' ' + coalesce(p.last_name,'')), p.name, p.uuid) AS name
ORDER BY toLower(name);
"""

def list_unassigned_persons(graph: Neo4jGraph):
    return graph.query(LIST_UNASSIGNED_PERSONS)

FIND_PERSONS_BY_SKILLS_ALL = """
WITH [x IN $skills | toLower(trim(x))] AS req
MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
WITH p, req, collect(DISTINCT toLower(trim(coalesce(s.name, s.title, s.id)))) AS personSkills
WHERE all(r IN req WHERE r IN personSkills)
RETURN
  p.uuid AS person_uuid,
  coalesce(p.full_name, trim(coalesce(p.first_name,'') + ' ' + coalesce(p.last_name,'')), p.name, p.uuid) AS name,
  [r IN req WHERE r IN personSkills] AS matchedSkills
ORDER BY toLower(name);
"""

FIND_PERSONS_BY_SKILLS_ANY = """
WITH [x IN $skills | toLower(trim(x))] AS req
MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
WITH p, req, collect(DISTINCT toLower(trim(coalesce(s.name, s.title, s.id)))) AS personSkills
WITH p, req, personSkills, [r IN req WHERE r IN personSkills] AS matched
WHERE size(matched) > 0
RETURN
  p.uuid AS person_uuid,
  coalesce(p.full_name, trim(coalesce(p.first_name,'') + ' ' + coalesce(p.last_name,'')), p.name, p.uuid) AS name,
  matched AS matchedSkills,
  size(matched) AS matchedCount
ORDER BY matchedCount DESC, toLower(name);
"""

def find_persons_by_skills(graph: Neo4jGraph, skills: list[str], mode: str = "all"):
    if not skills:
        return []
    mode = (mode or "all").lower()
    if mode not in ("all", "any"):
        raise ValueError("mode must be 'all' or 'any'")
    q = FIND_PERSONS_BY_SKILLS_ALL if mode == "all" else FIND_PERSONS_BY_SKILLS_ANY
    return graph.query(q, {"skills": skills})