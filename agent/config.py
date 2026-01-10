import os
from dataclasses import dataclass
from langchain_community.graphs import Neo4jGraph
@dataclass
class OpenAIConfig:
    api_key: str

@dataclass
class Neo4jConfig:
    uri: str
    user: str
    password: str

def get_openai_config() -> OpenAIConfig:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Brak zmiennej środowiskowej OPENAI_API_KEY")
    return OpenAIConfig(api_key=api_key)

def get_neo4j_config() -> Neo4jConfig:
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        raise RuntimeError("Brak zmiennej NEO4J_PASSWORD")
    return Neo4jConfig(uri=uri, user=user, password=password)

def init_neo4j() -> Neo4jGraph:
    config = get_neo4j_config()
    graph = Neo4jGraph(
        url = config.uri,
        username = config.user,
        password = config.password,
    )
    return graph
