# match_candidates.py
from dotenv import load_dotenv
import os
from langchain_neo4j import Neo4jGraph

#CORRUPTED
load_dotenv(override=True)


LIST_RFPS = """
MATCH (r:RFP)
RETURN r.id AS id, r.title AS title, r.client AS client
ORDER BY id;
"""

PERSON_KEYS_DEBUG = """
MATCH (p:Person)
RETURN keys(p) AS person_keys, count(*) AS cnt
ORDER BY cnt DESC
LIMIT 5;
"""

SKILL_KEYS_DEBUG = """
MATCH (s:Skill)
RETURN keys(s) AS skill_keys, count(*) AS cnt
ORDER BY cnt DESC
LIMIT 5;
"""

PERSON_SAMPLE = """
MATCH (p:Person)
RETURN p, coalesce(p.name, p.id, '(no-person-name)') AS display
LIMIT 5;
"""

LIST_PEOPLE_WITH_SKILLS = """
MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
WITH
  coalesce(p.name, p.id, '(no-person-name)') AS person_name,
  toLower(coalesce(s.name, s.title, s.id, '(no-skill-name)')) AS skill_name
RETURN person_name, collect(DISTINCT skill_name) AS skills
ORDER BY person_name;
"""


RFP_SKILLS_DEBUG = """
MATCH (r:RFP {id:$rfp_id})-[n:NEEDS]->(s:Skill)
WITH
  [x IN collect(CASE WHEN n.is_mandatory THEN toLower(coalesce(s.name, s.title, s.id)) END)
   WHERE x IS NOT NULL] AS mandatorySkills,
  [x IN collect(toLower(coalesce(s.name, s.title, s.id)))
   WHERE x IS NOT NULL] AS allRequiredSkills
RETURN mandatorySkills, allRequiredSkills;
"""


STRICT_MATCH_QUERY = """
MATCH (r:RFP {id:$rfp_id})-[n:NEEDS]->(s:Skill)
WITH
  [x IN collect(CASE WHEN n.is_mandatory THEN toLower(coalesce(s.name, s.title, s.id)) END)
   WHERE x IS NOT NULL] AS mandatorySkills,
  [x IN collect(toLower(coalesce(s.name, s.title, s.id)))
   WHERE x IS NOT NULL] AS allRequiredSkills

MATCH (p:Person)-[:HAS_SKILL]->(ps:Skill)
WITH p, mandatorySkills, allRequiredSkills,
     [x IN collect(toLower(coalesce(ps.name, ps.title, ps.id)))
      WHERE x IS NOT NULL] AS personSkills

WHERE all(ms IN mandatorySkills WHERE ms IN personSkills)

WITH p, allRequiredSkills, personSkills,
     [x IN allRequiredSkills WHERE x IN personSkills] AS matchedSkills,
     [x IN allRequiredSkills WHERE NOT x IN personSkills] AS missingSkills,
     size(allRequiredSkills) AS totalRequired

RETURN
  coalesce(p.name, p.id, '(no-person-name)') AS candidate,
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


SOFT_MATCH_QUERY = """
MATCH (r:RFP {id:$rfp_id})-[:NEEDS]->(s:Skill)
WITH
  [x IN collect(toLower(coalesce(s.name, s.title, s.id)))
   WHERE x IS NOT NULL] AS allRequiredSkills

MATCH (p:Person)-[:HAS_SKILL]->(ps:Skill)
WITH p, allRequiredSkills,
     [x IN collect(toLower(coalesce(ps.name, ps.title, ps.id)))
      WHERE x IS NOT NULL] AS personSkills

WITH p, allRequiredSkills, personSkills,
     [x IN allRequiredSkills WHERE x IN personSkills] AS matchedSkills,
     [x IN allRequiredSkills WHERE NOT x IN personSkills] AS missingSkills,
     size(allRequiredSkills) AS totalRequired

RETURN
  coalesce(p.name, p.id, '(no-person-name)') AS candidate,
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


def main():
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )

    rfps = graph.query(LIST_RFPS)
    if not rfps:
        print("❌ Brak RFP w grafie.")
        return

    print("\nDostępne RFP:")
    print("-" * 80)
    for r in rfps:
        print(f"{r['id']}: {r.get('title','')} | {r.get('client','')}")
    print("-" * 80)

    pk = graph.query(PERSON_KEYS_DEBUG)
    sk = graph.query(SKILL_KEYS_DEBUG)
    if pk:
        print("\nPerson keys:", pk[0]["person_keys"])
    if sk:
        print("Skill keys:", sk[0]["skill_keys"])

    people = graph.query(LIST_PEOPLE_WITH_SKILLS)
    print("\nOsoby i skille:")
    print("-" * 80)
    for row in people:
        skills = row["skills"] or []
        print(f"- {row['person_name']}: {', '.join(skills)}")
    print("-" * 80)

    rfp_id = input("\nPodaj RFP id: ").strip()
    if not rfp_id:
        return

    dbg = graph.query(RFP_SKILLS_DEBUG, {"rfp_id": rfp_id})
    if not dbg:
        print("❌ Nie znaleziono RFP.")
        return

    print("\nRFP skills:")
    print("Mandatory:", ", ".join(dbg[0]["mandatorySkills"]) or "(brak)")
    print("All req.: ", ", ".join(dbg[0]["allRequiredSkills"]) or "(brak)")

    rows = graph.query(STRICT_MATCH_QUERY, {"rfp_id": rfp_id})
    mode = "STRICT (mandatory)"

    if not rows:
        print("\nBrak wyników STRICT → SOFT ranking.")
        rows = graph.query(SOFT_MATCH_QUERY, {"rfp_id": rfp_id})
        mode = "SOFT (ranking)"

    if not rows:
        print("❌ Brak wyników.")
        return

    print(f"\nWyniki — tryb: {mode}")
    for i, r in enumerate(rows, 1):
        print("=" * 80)
        print(f"{i}. {r['candidate']} | {r['match_percent']}% ({r['matchedCount']}/{r['totalRequired']})")
        print("Matched:", ", ".join(r["matchedSkills"]) or "-")
        print("Missing:", ", ".join(r["missingSkills"]) or "-")


if __name__ == "__main__":
    main()
