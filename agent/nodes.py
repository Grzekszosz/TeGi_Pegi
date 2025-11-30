# agent/nodes.py
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from .state import RouterState
from .tools_graph import graph_cypher_query
from .config import get_openai_config

cfg = get_openai_config()

router_llm = ChatOpenAI(
    model="gpt-4o",
    api_key=cfg.api_key,
)

agent_llm = ChatOpenAI(
    model="gpt-4o",
    api_key=cfg.api_key,
).bind_tools([graph_cypher_query])

TOOLS_BY_NAME = {
    "graph_cypher_query": graph_cypher_query,
}

def classify_query(state: RouterState) -> Dict:
    messages = state["messages"]
    user_msg = messages[-1].content

    system_prompt = (
        "Twoje zadanie: zaklasyfikować zapytanie biznesowe HR/projektowe "
        "do jednego z typów:\n"
        "- counting\n- filtering\n- aggregation\n- reasoning\n- temporal\n- scenario\n\n"
        "Zwróć TYLKO jedno słowo z tej listy, bez żadnych wyjaśnień."
    )

    result = router_llm.invoke(
        [
            ("system", system_prompt),
            ("user", user_msg),
        ]
    )

    query_type = result.content.strip().lower()
    info_msg = AIMessage(content=f"[QUERY_TYPE:{query_type}]")

    return {
        "messages": messages + [info_msg],
        "query_type": query_type,
    }

def call_tools_and_answer(state: RouterState) -> Dict:
    # bierzemy historię z routera
    history = state["messages"][:]

    system_msg = (
        "Jesteś asystentem TalentMatch.\n"
        "- Masz dostęp do grafu wiedzy poprzez tool 'graph_cypher_query'.\n"
        "- Najpierw wymyśl zapytanie Cypher potrzebne do odpowiedzi.\n"
        "- Użyj toola, podając krótki opis i zapytanie Cypher.\n"
        "- Po otrzymaniu wyników z toola wygeneruj zrozumiałą odpowiedź biznesową po polsku.\n"
        "- Jeśli graf nie zawiera danych, powiedz o tym wprost."
    )

    messages_for_llm = [("system", system_msg)] + history

    # Pętla: LLM -> tool_calls -> uruchom toole -> LLM -> ... aż nie będzie tool_calls
    while True:
        ai_msg = agent_llm.invoke(messages_for_llm)
        messages_for_llm.append(ai_msg)

        tool_calls = getattr(ai_msg, "tool_calls", None)
        if not tool_calls:
            # brak wywołań tooli -> mamy finalną odpowiedź
            break

        # wykonujemy każde wywołanie toola
        for tc in tool_calls:
            name = tc["name"]
            args = tc["args"]
            tool_id = tc["id"]

            tool = TOOLS_BY_NAME.get(name)
            if tool is None:
                tool_result = f"Nieznane narzędzie: {name}"
            else:
                tool_result = tool.invoke(args)

            # dodajemy wynik toola jako ToolMessage
            tool_msg = ToolMessage(
                content=json.dumps(tool_result, ensure_ascii=False),
                tool_call_id=tool_id,
            )
            messages_for_llm.append(tool_msg)

    # Zapisujemy całą historię (bez systema) z powrotem w state
    # messages_for_llm[0] to system, reszta to historia użytkownika + router + agent
    new_messages = history + messages_for_llm[len(history) + 1:]

    return {"messages": new_messages}
