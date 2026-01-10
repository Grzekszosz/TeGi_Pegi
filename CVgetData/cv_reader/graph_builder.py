# cv_reader/graph_builder.py
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph
from langchain_core.documents import Document

from .pdf_reader import extract_text_from_pdf, list_cv_files


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
                "For Person nodes: extract and store these properties if present: "
                "first_name, last_name, email, location. "
                "If a value is missing in the CV, leave it null/empty; do NOT guess. "
                "Do NOT use arbitrary tokens as a person's name."
            ),
        )

    def normalize_uid(self):
        self.graph.query("MATCH (p:Person) WHERE p.uuid IS NULL SET p.uuid = randomUUID();")

    # opcjonalnie: wyczyść bazę przed startem
    def reset_graph(self):
        self.graph.query("MATCH (n) DETACH DELETE n")

    def cv_text_to_document(self, pdf_path: Path) -> Document:
        """PDF -> tekst -> Document dla LLM."""
        text = extract_text_from_pdf(pdf_path)
        return Document(
            page_content=text,
            metadata={"source": pdf_path.name},
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


    def process_single_cv(self, pdf_path: Path):
        """Pełny flow dla jednego CV."""
        print(f"Przetwarzam CV: {pdf_path.name}")
        graph_docs = self.cv_to_graph_documents(pdf_path)
        self.store_graph_documents(graph_docs)

    def process_all_cvs(self):
        """Przetwórz wszystkie PDF-y z data/cvs."""
        pdf_files = list_cv_files()
        if not pdf_files:
            print("Brak plików CV w data/cvs/")
            return

        for pdf in pdf_files:
            self.process_single_cv(pdf)

        self.normalize_uid()
        print("Gotowe! Sprawdź graf w Neo4j Browser 🙂")
