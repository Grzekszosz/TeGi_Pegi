from langchain_neo4j import Neo4jGraph

ASSIGN_QUERY = """
MATCH (p:Person {uuid:$person_uuid})
MATCH (r:RFP {id:$rfp_id})
WITH p, r,
     date($start_date) AS newStart,
     date($end_date) AS newEnd,
     toFloat($allocation) AS newAlloc

// policz ile już ma w tym oknie
OPTIONAL MATCH (p)-[a:ASSIGNED_TO]->(r2:RFP)
WHERE a.startDate <= newEnd AND a.endDate >= newStart
WITH p, r, newStart, newEnd, newAlloc,
     sum(coalesce(a.allocation, 0.0)) AS alreadyAllocated,
     collect({rfp_id:r2.id, title:r2.title, alloc:a.allocation, start:toString(a.startDate), end:toString(a.endDate)}) AS overlaps

// warunek hamulca
CALL apoc.util.validate(
  alreadyAllocated + newAlloc > 1.0,
  'Allocation conflict: alreadyAllocated=%.2f, requested=%.2f, overlaps=%s',
  [alreadyAllocated, newAlloc, overlaps]
)

CREATE (p)-[as:ASSIGNED_TO]->(r)
SET as.id = randomUUID(),
    as.role = $role,
    as.allocation = newAlloc,
    as.startDate = newStart,
    as.endDate = newEnd,
    as.createdAt = datetime(),
    as.updatedAt = datetime()

RETURN
  coalesce(p.full_name, p.uuid) AS person,
  p.uuid AS person_uuid,
  coalesce(r.title, r.id) AS rfp,
  as.role AS role,
  as.allocation AS allocation,
  toString(as.startDate) AS startDate,
  toString(as.endDate) AS endDate;
"""

def assign_person_to_rfp(
    graph: Neo4jGraph,
    person_uuid: str,
    rfp_id: str,
    role: str,
    allocation: float,
    start_date: str,
    end_date: str,
):
    alloc = float(allocation)

    if alloc > 1.0 and alloc <= 100.0:
        alloc = alloc / 100.0

    if not (0 < alloc <= 1.0):
        raise ValueError("allocation must be in (0,1] or 1..100 percent")

    return graph.query(ASSIGN_QUERY, {
        "person_uuid": person_uuid,
        "rfp_id": rfp_id,
        "role": role,
        "allocation": float(allocation),
        "start_date": start_date,
        "end_date": end_date,
    })

LIST_ASSIGNED_QUERY = """
MATCH (p:Person)-[a:ASSIGNED_TO]->(r:RFP {id:$rfp_id})
RETURN
  r.id AS rfp_id,
  coalesce(r.title, r.id) AS rfp_title,
  coalesce(p.full_name, trim(coalesce(p.first_name,'') + ' ' + coalesce(p.last_name,'')), p.uuid) AS person,
  p.uuid AS person_uuid,
  a.role AS role,
  a.allocation AS allocation,
  toString(a.startDate) AS start_date,
  toString(a.endDate) AS end_date,
  toString(a.updatedAt) AS updated_at
ORDER BY a.startDate, person;
"""

def list_assigned_people(graph: Neo4jGraph, rfp_id: str):
    return graph.query(LIST_ASSIGNED_QUERY, {"rfp_id": rfp_id})

LIST_PROJECT_ASSIGNMENTS = """
MATCH (r:RFP)
OPTIONAL MATCH (p:Person)-[a:ASSIGNED_TO]->(r)
WITH r,
     collect(
       CASE WHEN p IS NULL THEN NULL ELSE {
         person_uuid: p.uuid,
         person: coalesce(p.full_name, trim(coalesce(p.first_name,'') + ' ' + coalesce(p.last_name,'')), p.uuid),
         role: a.role,
         allocation: a.allocation,
         start_date: toString(a.startDate),
         end_date: toString(a.endDate)
       } END
     ) AS assigned_raw
WITH r, [x IN assigned_raw WHERE x IS NOT NULL] AS assigned
WITH r, assigned,
     CASE
       WHEN r.start_date IS NULL OR trim(toString(r.start_date)) = "" THEN NULL
       ELSE date(toString(r.start_date))
     END AS startDate
WITH r, assigned, startDate,
     CASE
       WHEN startDate IS NULL OR r.duration_months IS NULL THEN NULL
       ELSE startDate + duration({months: toInteger(r.duration_months)})
     END AS endDate
RETURN
  r.id AS id,
  r.title AS name,
  r.client AS client,
  r.project_type AS project_type,
  toString(startDate) AS start_date,
  toString(endDate) AS end_date,
  r.team_size AS team_size,
  size(assigned) AS assigned_count,
  assigned
ORDER BY coalesce(startDate, date('9999-12-31')), id;
"""

def list_project_assignments(graph: Neo4jGraph):
    return graph.query(LIST_PROJECT_ASSIGNMENTS)

LIST_PROJECT_ASSIGNMENTS_QUERY_TO_RFP = """
    MATCH (p:Person)
    WHERE NOT (p)-[:ASSIGNED_TO]->(:RFP {id:$rfp_id})
    RETURN p.uuid AS person_uuid,
           coalesce(p.full_name, trim(coalesce(p.first_name,'') + ' ' + coalesce(p.last_name,'')), p.name, p.uuid) AS name
    ORDER BY toLower(name);
    """
def list_project_assignments_to_rfp(graph: Neo4jGraph,rfp_id: str ):
    return graph.query(LIST_PROJECT_ASSIGNMENTS_QUERY_TO_RFP,{"rfp_id": rfp_id})


EXPLAIN_MATCH = """
MATCH (r:RFP {id:$rfp_id})
WITH r,
     CASE
       WHEN r.start_date IS NULL OR trim(toString(r.start_date)) = "" THEN NULL
       ELSE date(toString(r.start_date))
     END AS projStart
WITH r, projStart,
     CASE
       WHEN projStart IS NULL OR r.duration_months IS NULL THEN NULL
       ELSE projStart + duration({months: toInteger(r.duration_months)})
     END AS projEnd

MATCH (p:Person {uuid:$person_uuid})

// wymagane skille + mandatory
OPTIONAL MATCH (r)-[n:NEEDS]->(rs:Skill)
WITH r, p, projStart, projEnd,
     collect(DISTINCT {
       skill: toLower(trim(coalesce(rs.name, rs.title, rs.id))),
       mandatory: coalesce(n.is_mandatory,false)
     }) AS reqs

// skille osoby
OPTIONAL MATCH (p)-[:HAS_SKILL]->(ps:Skill)
WITH r, p, projStart, projEnd, reqs,
     collect(DISTINCT toLower(trim(coalesce(ps.name, ps.title, ps.id)))) AS personSkills

WITH r, p, projStart, projEnd, reqs, personSkills,
     [x IN reqs WHERE x.mandatory] AS mandatoryReqs,
     [x IN reqs | x.skill] AS allReqSkills

WITH r, p, projStart, projEnd, personSkills,
     [x IN mandatoryReqs | x.skill] AS mandatorySkills,
     allReqSkills

WITH r, p, projStart, projEnd, personSkills, mandatorySkills, allReqSkills,
     [x IN allReqSkills WHERE x IN personSkills] AS matchedSkills,
     [x IN allReqSkills WHERE NOT x IN personSkills] AS missingSkills,
     all(ms IN mandatorySkills WHERE ms IN personSkills) AS mandatory_pass

// availability w oknie projektu
OPTIONAL MATCH (p)-[a:ASSIGNED_TO]->(:RFP)
WHERE projStart IS NOT NULL AND projEnd IS NOT NULL
  AND a.startDate <= projEnd AND a.endDate >= projStart
WITH r, p, projStart, projEnd, personSkills, mandatorySkills, allReqSkills,
     matchedSkills, missingSkills, mandatory_pass,
     sum(coalesce(a.allocation, 0.0)) AS allocated

WITH r, p, projStart, projEnd,
     mandatory_pass,
     matchedSkills, missingSkills, mandatorySkills, allReqSkills,
     allocated,
     round(1.0 - allocated, 2) AS available,
     size(allReqSkills) AS totalRequired

RETURN
  r.id AS rfp_id,
  r.title AS rfp_title,
  toString(projStart) AS project_start,
  toString(projEnd) AS project_end,
  p.uuid AS person_uuid,
  coalesce(p.full_name, p.name, p.uuid) AS person_name,

  mandatory_pass,
  mandatorySkills,
  matchedSkills,
  missingSkills,

  totalRequired,
  size(matchedSkills) AS matchedCount,
  CASE WHEN totalRequired = 0 THEN 0.0
       ELSE round(100.0 * size(matchedSkills) / totalRequired, 1) END AS match_percent,

  allocated AS allocated_fte,
  available AS available_fte;
  """

def explain_match(graph: Neo4jGraph, rfp_id: str, person_uuid: str):
    rows = graph.query(EXPLAIN_MATCH, {"rfp_id": rfp_id, "person_uuid": person_uuid})
    return rows[0] if rows else None