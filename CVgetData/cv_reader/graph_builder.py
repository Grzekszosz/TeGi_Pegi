# cv_reader/graph_builder.py
from __future__ import annotations

import os
from pathlib import Path


from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph
from langchain_core.documents import Document

from .cv_parser import parse_cv
from .pdf_reader import list_cv_files
from CVgetData.text_extractor import extract_text_auto


load_dotenv(override=True)


class CVGraphBuilder:


    def __init__(self):
        # --- LLM ---
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )

        # --- Neo4j ---
        self.graph = Neo4jGraph(
            url=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD"),
        )
        # --- Transformer: tekst -> graf ---
        self.transformer = LLMGraphTransformer(
            llm=self.llm,
            allowed_nodes=[
                "Person",
                "Company",
                "Skill",
                "JobTitle",
                "Location",
                "Education",
                "Language",
                "Project",
            ],
            allowed_relationships=[
                "WORKED_AT",      # Person -> Company
                "HAS_SKILL",      # Person -> Skill
                "HAS_TITLE",      # Person -> JobTitle
                "LIVES_IN",       # Person -> Location
                "STUDIED_AT",     # Person -> Education
                "SPEAKS_LANGUAGE",# Person -> Language
                "WORKED_ON",      # Person -> Project
            ],
            additional_instructions=(
                "You will receive a CV that can be written in Polish or English. "
                "Output graph data MUST be in English.\n"
                "- Node labels and relationship types MUST be exactly one of the allowed lists.\n"
                "- Translate Polish entity values to English (job titles, skills, education fields, project descriptions).\n"
                "- Keep proper nouns (person/company names, product names, certificates) in original form unless there is a standard English name.\n"
                "- Normalize synonyms to a single canonical English term (e.g., 'C# developer' vs 'Software Engineer').\n"
                "- Do not invent facts not present in the CV."
                "- For Person nodes: extract and store these properties if present: "
                "- first_name, last_name, email, location. "
                "- If a value is missing in the CV, leave it null/empty; do NOT guess. "
                "- Do NOT use arbitrary tokens as a person's name."
            ),
        )

    def normalize_uid(self):
        self.graph.query("MATCH (p:Person) WHERE p.uuid IS NULL SET p.uuid = randomUUID();")

    # opcjonalnie: wyczyść bazę przed startem
    def reset_graph(self):
        self.graph.query("MATCH (n) DETACH DELETE n")

    def cv_text_to_document(self, path: Path) -> Document:
        """PDF -> tekst -> Document dla LLM."""
        text = extract_text_auto(path)

        return Document(
            page_content=text,
            metadata={"source": path.name},
        )

    def cv_to_graph_documents(self, pdf_path: Path):
        """Jedno CV -> lista graph_documents (węzły + relacje)."""
        doc = self.cv_text_to_document(pdf_path)
        graph_docs = self.transformer.convert_to_graph_documents([doc])
        return graph_docs

    def store_graph_documents(self, graph_docs):
        """Zapisz graph_documents do Neo4j."""
        # Twoja wersja Neo4jGraph nie przyjmuje już base_entity_label / include_source
        self.graph.add_graph_documents(graph_docs)

    def upsert_cv_anchor(self, source: str):
        # tworzymy węzeł CV - kotwica pod aktualizacje
        self.graph.query(
            """
            MERGE (cv:CV {source: $source})
            SET cv.ingested_at = datetime()
            """,
            params={"source": source},
        )

    def link_person_to_cv(self, source: str):
        """
        Po imporcie graph_docs próbujemy podpiąć Person pod CV.
        MVP: bierzemy jedną Person bez FROM_CV i przypinamy do CV.
        To jest proste i działa, dopóki import jednego CV daje jedną osobę.
        """
        self.graph.query(
            """
            MATCH (cv:CV {source: $source})
            MATCH (p:Person)
            WHERE NOT (p)-[:FROM_CV]->(:CV)
            WITH cv, p
            LIMIT 1
            MERGE (p)-[:FROM_CV]->(cv)
            """,
            params={"source": source},
        )


    def update_person_skills(self, source: str, skills_graph: list[str], skills_fallback: list[str]):
        # wybierz preferowane: graf > fallback
        final_skills = skills_graph if skills_graph else skills_fallback

        self.graph.query(
            """
            MATCH (p:Person)-[:FROM_CV]->(cv:CV {source: $source})
            SET p.skills = $skills
            """,
            params={"source": source, "skills": final_skills},
        )



    def update_person_core_from_parsed(self, source: str, parsed: dict):
        """
        Dopisuje pola do Person powiązanego z CV.
        """

        self.graph.query(
            """
            MATCH (p:Person)-[:FROM_CV]->(cv:CV {source: $source})
            SET
              p.email = coalesce(p.email, $email),
              p.skills = coalesce(p.skills, $skills)
            """,
            params={
                "source": source,
                "email": parsed.get("email"),
                "skills": parsed.get("skills", []),
                "projects" : parsed.get("projects", []),
            },
        )

    def normalize_person_name(self, source: str):
        """
        Uzupełnia first_name/last_name na podstawie p.id (np. "Mohsen Lahf"),
        ale tylko dla osoby powiązanej z danym CV.
        """
        self.graph.query(
            """
            MATCH (p:Person)-[:FROM_CV]->(cv:CV {source: $source})
            WHERE (p.first_name IS NULL OR trim(p.first_name) = "")
              AND (p.last_name  IS NULL OR trim(p.last_name)  = "")
              AND p.id IS NOT NULL
              AND NOT toLower(p.id) IN [
                "kontakt","doświadczenie","experience","skills","umiejętności",
                "education","wykształcenie","projects","project","languages","języki"
              ]
            WITH p, split(trim(p.id), " ") AS parts
            WHERE size(parts) >= 2 AND size(parts) <= 4
            SET p.first_name = parts[0],
                p.last_name  = parts[-1],
                p.full_name  = trim(p.id)
            """,
            params={"source": source},
        )

    def cleanup_person_ids(self, source: str):
        self.graph.query(
            """
            MATCH (p:Person)-[:FROM_CV]->(cv:CV {source: $source})
            REMOVE p.id
            REMOVE p.`<id>`
            """,
            params={"source": source},
        )

    def get_person_skills_from_graph(self, source: str) -> list[str]:
        rows = self.graph.query(
            """
            MATCH (p:Person)-[:FROM_CV]->(cv:CV {source: $source})
            OPTIONAL MATCH (p)-[:HAS_SKILL]->(s:Skill)
            WITH collect(DISTINCT coalesce(s.name, s.id)) AS skills
            RETURN [x IN skills WHERE x IS NOT NULL AND trim(toString(x)) <> ""] AS skills
            """,
            params={"source": source},
        )
        if not rows:
            return []
        return rows[0].get("skills", []) or []

    def ensure_skill_relationships(self, source: str, skills: list[str]):
        if not skills:
            return

        self.graph.query(
            """
            MATCH (p:Person)-[:FROM_CV]->(cv:CV {source: $source})
            UNWIND $skills AS skill
            WITH p, trim(skill) AS sname
            WHERE sname <> ""
            MERGE (s:Skill {name: sname})
            MERGE (p)-[:HAS_SKILL]->(s)
            """,
            params={"source": source, "skills": skills},
        )

    def sync_person_skills_property_from_graph(self, source: str):
        self.graph.query(
            """
            MATCH (p:Person)-[:FROM_CV]->(cv:CV {source: $source})
            OPTIONAL MATCH (p)-[:HAS_SKILL]->(s:Skill)
            WITH p, collect(DISTINCT coalesce(s.name, s.id)) AS skills
            SET p.skills = [x IN skills WHERE x IS NOT NULL AND trim(toString(x)) <> ""]
            """,
            params={"source": source},
        )



    def process_single_cv(self, pdf_path: Path):

        print(f"Przetwarzam CV: {pdf_path.name}")

        # 1) PDF -> tekst
        doc = self.cv_text_to_document(pdf_path)
        text = doc.page_content
        source = pdf_path.name

        # 2) Kotwica CV
        self.upsert_cv_anchor(source)

        # 3) Transformer -> graf
        graph_docs = self.transformer.convert_to_graph_documents([doc])
        self.store_graph_documents(graph_docs)

        # 4) Połącz Person z CV (MVP)
        self.link_person_to_cv(source)

        # 5) Deterministyczne pola
        parsed = parse_cv(text)
        self.update_person_core_from_parsed(source, parsed)

        self.normalize_person_name(source)

        self.cleanup_person_ids(source)

        skills_graph = self.get_person_skills_from_graph(source)

        if not skills_graph:
            # 5a) jeśli transformer nie dopiął HAS_SKILL, dopnij z fallbacku
            self.ensure_skill_relationships(source, parsed.get("skills_fallback", []))

        # 5b) na koniec: zsynchronizuj property p.skills z relacji HAS_SKILL
        self.sync_person_skills_property_from_graph(source)


    def process_all_cvs(self):
        """Przetwórz wszystkie PDF-y z data/cvs."""

        pdf_files = list_cv_files(Path(__file__).resolve().parent.parent / "data/cvs")

        for f in pdf_files:
            print(f)

        if not pdf_files:
            print("Brak plików CV w data/cvs/")
            return

        for pdf in pdf_files:
            self.process_single_cv(pdf)

        self.normalize_uid()
        print("Gotowe! Sprawdź graf w Neo4j Browser 🙂")
