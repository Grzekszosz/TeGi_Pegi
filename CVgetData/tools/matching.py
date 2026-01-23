from langchain_neo4j import Neo4jGraph

LIST_RFPS = """MATCH (r:RFP) RETURN r.uuid AS uuid, r.title AS title, r.client AS client ORDER BY uuid;"""

LIST_RFPS_WITH_SKILLS = """
MATCH (r:RFP)
OPTIONAL MATCH (r)-[:NEEDS]->(s:Skill)
WITH r, collect(DISTINCT s.name) AS skills
RETURN r.uuid AS uuid, r.title AS title, r.client AS client,
       r.project_type AS project_type,
       skills
ORDER BY uuid;
"""

STRICT_MATCH_QUERY = """
MATCH (r:RFP {uuid:$rfp_uuid})-[n:NEEDS]->(s:Skill)
WITH
  [x IN collect(CASE WHEN n.is_mandatory THEN toLower(coalesce(s.name, s.title, s.uuid)) END)
   WHERE x IS NOT NULL] AS mandatorySkills,
  [x IN collect(toLower(coalesce(s.name, s.title, s.uuid)))
   WHERE x IS NOT NULL] AS allRequiredSkills

MATCH (p:Person)-[:HAS_SKILL]->(ps:Skill)
WITH p, mandatorySkills, allRequiredSkills,
     [x IN collect(toLower(coalesce(ps.name, ps.title, ps.uuid)))
      WHERE x IS NOT NULL] AS personSkills

WHERE all(ms IN mandatorySkills WHERE ms IN personSkills)

WITH p, allRequiredSkills, personSkills,
     [x IN allRequiredSkills WHERE x IN personSkills] AS matchedSkills,
     [x IN allRequiredSkills WHERE NOT x IN personSkills] AS missingSkills,
     size(allRequiredSkills) AS totalRequired

RETURN
  coalesce(p.uuid, p.person_uuid, p.uuuuid) AS person_uuid,
  coalesce(p.name, p.full_name, p.uuid, p.person_uuid, p.uuuuid, '(no-person-name)') AS canduuidate,
  size(matchedSkills) AS matchedCount,
  totalRequired,
  CASE
    WHEN totalRequired = 0 THEN 0.0
    ELSE round(100.0 * size(matchedSkills) / totalRequired, 1)
  END AS match_percent,
  matchedSkills,
  missingSkills
ORDER BY match_percent DESC, matchedCount DESC
LIMIT 20;
"""
SOFT_MATCH_QUERY   = """
MATCH (r:RFP {uuid:$rfp_uuid})-[:NEEDS]->(s:Skill)
WITH
  [x IN collect(toLower(coalesce(s.name, s.title, s.uuid)))
   WHERE x IS NOT NULL] AS allRequiredSkills

MATCH (p:Person)-[:HAS_SKILL]->(ps:Skill)
WITH p, allRequiredSkills,
     [x IN collect(toLower(coalesce(ps.name, ps.title, ps.uuid)))
      WHERE x IS NOT NULL] AS personSkills

WITH p, allRequiredSkills, personSkills,
     [x IN allRequiredSkills WHERE x IN personSkills] AS matchedSkills,
     [x IN allRequiredSkills WHERE NOT x IN personSkills] AS missingSkills,
     size(allRequiredSkills) AS totalRequired

RETURN
  coalesce(p.uuid, p.person_uuid, p.uuuuid) AS person_uuid,
  coalesce(p.name, p.full_name, p.uuid, p.person_uuid, p.uuuuid, '(no-person-name)') AS canduuidate,
  size(matchedSkills) AS matchedCount,
  totalRequired,
  CASE
    WHEN totalRequired = 0 THEN 0.0
    ELSE round(100.0 * size(matchedSkills) / totalRequired, 1)
  END AS match_percent,
  matchedSkills,
  missingSkills
ORDER BY match_percent DESC, matchedCount DESC
LIMIT 20;
"""

def list_rfps(graph: Neo4jGraph):
    return graph.query(LIST_RFPS)

def list_rfps_with_skills(graph: Neo4jGraph):
    return graph.query(LIST_RFPS_WITH_SKILLS)

def match_rfp(graph: Neo4jGraph, rfp_uuid: str, mode: str = "auto", limit: int = 20):
    if mode not in ("auto", "strict", "soft"):
        raise ValueError("mode must be auto/strict/soft")

    rows = []
    used_mode = None

    if mode in ("auto", "strict"):
        rows = graph.query(STRICT_MATCH_QUERY, {"rfp_uuid": rfp_uuid})
        used_mode = "strict"

    if (not rows) and mode in ("auto", "soft"):
        rows = graph.query(SOFT_MATCH_QUERY, {"rfp_uuid": rfp_uuid})
        used_mode = "soft"

    return {"mode": used_mode, "results": rows[:limit]}
