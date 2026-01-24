from dotenv import load_dotenv
import os
import sys
from langchain_community.graphs import Neo4jGraph
from CVgetData.build_graph_from_rfps import build_rfps
from CVgetData.cv_reader.graph_builder import CVGraphBuilder

load_dotenv()

def fail(msg, exc=None):
    print(f"[test_neo4j_connection] ERROR: {msg}")
    if exc:
        print(f"[test_neo4j_connection] {type(exc).__name__}: {exc}")
    sys.exit(1)

try:
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )

    result = graph.query("RETURN 1 AS test")

    if not result or result[0].get("test") != 1:
        fail("Neo4j responded, but result is invalid")

    print("[test_neo4j_connection] Neo4j connection OK")

    result = graph.query("MATCH (n) RETURN count(n) AS cnt")
    count = result[0]["cnt"]

    if (count == 0 or count == 1):
        print ("[test_neo4j_connection] Neo4j looks empty initialize fullfilment")
        builder = CVGraphBuilder()
        builder.reset_graph()
        builder.process_all_cvs()
        build_rfps()
except Exception as e:
    fail("Neo4j connection failed", e)

sys.exit(0)
