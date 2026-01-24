from dotenv import load_dotenv
import os
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain

def main():
    load_dotenv()

    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD"),
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )

    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        allow_dangerous_requests=True,
    )

    print("Zapytaj o coś z grafu CV (ENTER żeby wyjść)\n")

    while True:
        question = input("❓ Pytanie: ")
        if not question.strip():
            break

        answer = chain.run(question)
        print("\n Odpowiedź:\n", answer)


if __name__ == "__main__":
    main()
