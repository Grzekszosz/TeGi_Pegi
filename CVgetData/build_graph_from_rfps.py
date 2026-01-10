from dotenv import load_dotenv
import os

from langchain_community.graphs import Neo4jGraph

from rfp_reader.pdf_reader import list_rfp_files, extract_text_from_pdf
from rfp_reader.rfp_extractor import extract_rfp_json

load_dotenv(override=True)

def build_rfps():
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
        text = extract_text_from_pdf(f)
        rfp = extract_rfp_json(text)

        # 1) RFP node
        graph.query("""
        MERGE (r:RFP {id:$id})
        SET r.title=$title,
            r.client=$client,
            r.description=$description,
            r.project_type=$project_type,
            r.duration_months=$duration_months,
            r.team_size=$team_size,
            r.budget_range=$budget_range,
            r.start_date=$start_date,
            r.location=$location,
            r.remote_allowed=$remote_allowed
        """, rfp.model_dump())

        # 2) Requirements -> Skill nodes + NEEDS rel
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
                "rfp_id": rfp.id,
                **req.model_dump()
            })

    print("Gotowe! RFP-y zapisane do Neo4j.")

if __name__ == "__main__":
    build_rfps()
