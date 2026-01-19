from agent.config import OpenAIConfig, get_neo4j_config, get_openai_config, init_neo4j

def get_persons():
    try:
        graph = init_neo4j()
        query = """
        MATCH (p:Person)
        OPTIONAL MATCH (p)-[:LIVES_IN]->(l:Location)
        WITH p,
             coalesce(p.first_name, p.firstname, p.given_name) AS first,
             coalesce(p.last_name,  p.lastname,  p.surname, p.family_name) AS last,
             coalesce(p.email, p.mail) AS email,
             coalesce(p.location, l.name, l.id) AS location
        RETURN
             trim(coalesce(first,'') + ' ' + coalesce(last,'')) AS full_name,
             email,
             location,
             p.uuid AS uuid
        ORDER BY (email IS NULL), full_name
        """
        return graph.query(query)
    except Exception as exc:
        print(f"[get_persons] {type(exc).__name__}: {exc}")
        return []

def count_persons():
    try:
        graph = init_neo4j()
        query = """
        MATCH (p:Person)
        RETURN count(p)
        """
        return graph.query(query)
    except Exception as exc:
        print(f"[count_persons] {type(exc).__name__}: {exc}")