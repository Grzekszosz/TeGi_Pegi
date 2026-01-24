from langchain_neo4j import Neo4jGraph

AVG_PROJECT_DURATION = """
MATCH (r:RFP)
WHERE r.duration_months IS NOT NULL
WITH toFloat(r.duration_months) AS m
RETURN
  count(*) AS projects_count,
  round(avg(m), 2) AS avg_duration_months,
  round(min(m), 2) AS min_duration_months,
  round(max(m), 2) AS max_duration_months,
  round(percentileCont(m, 0.5), 2) AS median_duration_months;
"""

def avg_project_duration(graph: Neo4jGraph):
    rows = graph.query(AVG_PROJECT_DURATION)
    return rows[0] if rows else None


AVAILABILITY_IN_WINDOW = """
WITH date($start_date) AS winStart,
     date($end_date)   AS winEnd,
     toFloat($min_available) AS minAvail

MATCH (p:Person)
OPTIONAL MATCH (p)-[a:ASSIGNED_TO]->(:RFP)
WHERE a.startDate <= winEnd AND a.endDate >= winStart
WITH p, winStart, winEnd, minAvail,
     sum(coalesce(a.allocation, 0.0)) AS allocated

WITH p,
     allocated,
     round(1.0 - allocated, 2) AS available
WHERE available >= minAvail

RETURN
  p.uuid AS person_uuid,
  coalesce(
    p.full_name,
    trim(coalesce(p.first_name,'') + ' ' + coalesce(p.last_name,'')),
    p.name,
    p.uuid
  ) AS name,
  allocated AS allocated_fte,
  available AS available_fte
ORDER BY available DESC, toLower(name);
"""
def find_available_persons(
    graph: Neo4jGraph,
    start_date: str,
    end_date: str,
    min_available: float = 1.0,
):
    return graph.query(
        AVAILABILITY_IN_WINDOW,
        {
            "start_date": start_date,
            "end_date": end_date,
            "min_available": min_available,
        },
    )

PIPELINE_SKILL_GAPS = """
WITH date($from) AS fromD, date($to) AS toD

MATCH (r:RFP)
WITH r,
     CASE
       WHEN r.start_date IS NULL OR trim(toString(r.start_date)) = "" THEN NULL
       ELSE date(toString(r.start_date))
     END AS startDate,
     fromD, toD
WHERE startDate IS NOT NULL AND startDate >= fromD AND startDate <= toD

MATCH (r)-[n:NEEDS]->(s:Skill)
WITH
  toLower(trim(coalesce(s.name, s.title, s.id))) AS skill,
  sum(CASE WHEN coalesce(n.is_mandatory,false) THEN 1 ELSE 0 END) AS mandatory_reqs,
  count(*) AS total_reqs,
  count(DISTINCT r.id) AS projects_count

OPTIONAL MATCH (p:Person)-[:HAS_SKILL]->(ps:Skill)
WHERE toLower(trim(coalesce(ps.name, ps.title, ps.id))) = skill
WITH
  skill, mandatory_reqs, total_reqs, projects_count,
  count(DISTINCT p.uuid) AS people_with_skill

RETURN
  skill,
  projects_count,
  mandatory_reqs,
  total_reqs,
  people_with_skill,
  (mandatory_reqs - people_with_skill) AS mandatory_gap,
  (total_reqs - people_with_skill) AS total_gap
ORDER BY mandatory_gap DESC, total_gap DESC, total_reqs DESC, skill
LIMIT coalesce($limit, 50);
"""

def pipeline_skill_gaps(graph: Neo4jGraph, from_date: str, to_date: str, limit: int = 50):
    return graph.query(PIPELINE_SKILL_GAPS, {"from": from_date, "to": to_date, "limit": limit})