from pathlib import Path

from dotenv import load_dotenv
import os

from langchain_community.graphs import Neo4jGraph

from CVgetData.cv_reader.graph_builder import CVGraphBuilder
from CVgetData.text_extractor import extract_text_auto
from CVgetData.rfp_reader.pdf_reader import list_rfp_files
from CVgetData.rfp_reader.rfp_extractor import extract_rfp_json

load_dotenv(override=True)

def build_rfps():

    #onyl this time
    builder = CVGraphBuilder()
    #builder.reset_graph()

    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )

    files = list_rfp_files()
    if not files:
        print("Brak RFP PDF w data/rfps/")
        return

    for f in files:
        print("Przetwarzam RFP:", f.name)
        try:
            text= extract_text_auto(f)
        except Exception as e:
            print(f"{type(e).__name__}: {e}")

        text = text.replace("Request for Proposal (RFP)", "")

        rfp = extract_rfp_json(text)

        source = f.name
        data = rfp.model_dump()
        data["id"] = source  # klucz MERGE = unikalny per plik
        data["source"] = source  # fajne do debugowania

        graph.query("""
        MERGE (r:RFP {id:$id})
        SET r.source=$source,
            r.title=$title,
            r.client=$client,
            r.description=$description,
            r.project_type=$project_type,
            r.duration_months=$duration_months,
            r.team_size=$team_size,
            r.budget_range=$budget_range,
            r.start_date=$start_date,
            r.location=$location,
            r.remote_allowed=$remote_allowed
        """, data)

        for req in rfp.requirements:
            graph.query("""
            MERGE (s:Skill {name:$skill_name})
            WITH s
            MATCH (r:RFP {id:$rfp_id})
            MERGE (r)-[rel:NEEDS]->(s)
            SET rel.min_proficiency=$min_proficiency,
                rel.is_mandatory=$is_mandatory,
                rel.preferred_certifications=$preferred_certifications
            """, {
                "rfp_id": source,  # <-- też source, nie rfp.id
                **req.model_dump()
            })

    print("Gotowe! RFP-y zapisane do Neo4j.")

def build_rfp(path: Path):
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )
    try:
        text = extract_text_auto(path)
    except Exception as e:
        print(f"{type(e).__name__}: {e}")

    text = text.replace("Request for Proposal (RFP)", "")

    rfp = extract_rfp_json(text)

    source = path.name
    data = rfp.model_dump()
    data["id"] = source  # klucz MERGE = unikalny per plik
    data["source"] = source  # fajne do debugowania

    graph.query("""
    MERGE (r:RFP {id:$id})
    SET r.source=$source,
        r.title=$title,
        r.client=$client,
        r.description=$description,
        r.project_type=$project_type,
        r.duration_months=$duration_months,
        r.team_size=$team_size,
        r.budget_range=$budget_range,
        r.start_date=$start_date,
        r.location=$location,
        r.remote_allowed=$remote_allowed
    """, data)

    for req in rfp.requirements:
        graph.query("""
        MERGE (s:Skill {name:$skill_name})
        WITH s
        MATCH (r:RFP {id:$rfp_id})
        MERGE (r)-[rel:NEEDS]->(s)
        SET rel.min_proficiency=$min_proficiency,
            rel.is_mandatory=$is_mandatory,
            rel.preferred_certifications=$preferred_certifications
        """, {
            "rfp_id": source,  # <-- też source, nie rfp.id
            **req.model_dump()
        })


if __name__ == "__main__":
    build_rfps()
