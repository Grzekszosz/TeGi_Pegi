from agent.config import init_neo4j


def get_rfps():
    try:
        graph = init_neo4j()

        query = """
        MATCH (r:RFP)
        RETURN
          r.project_title AS `Project Title`,
          r.start_date    AS `Start Date`,
          r.duration      AS `Duration`,
          r.team_size     AS `Team Size`,
          r.budget_range  AS `Budget Range`,
          r.uuid          AS uuid
        ORDER BY `Start Date` DESC, `Project Title`
        """

        return graph.query(query)

    except Exception as exc:
        print(f"[get_rfps] {type(exc).__name__}: {exc}")
        return []
