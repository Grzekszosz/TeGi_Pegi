# agent/nodes.py
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from CVgetData.tools.persons import get_person_graph, search_persons
from .state import RouterState
from .tools_graph import (graph_cypher_query, tool_assign_person, tool_match_rfp, tool_list_rfps, tool_list_persons,
                          tool_get_person_graph, tool_search_person, tool_list_assigned_people,
                          tool_list_unassigned_persons, tool_list_persons_not_in_rfp, tool_find_persons_by_skills,
                          tool_avg_project_duration, tool_find_available_persons, tool_pipeline_skill_gaps,
                          tool_explain_match)
from .config import get_openai_config

cfg = get_openai_config()

router_llm = ChatOpenAI(
    model="gpt-4o",
    api_key=cfg.api_key,
)

agent_llm = ChatOpenAI(
    model="gpt-4o",
    api_key=cfg.api_key,
).bind_tools([tool_list_rfps,
              tool_match_rfp,
              tool_assign_person,
              tool_list_persons,
              tool_get_person_graph,
              tool_search_person,
              tool_list_assigned_people,
              tool_list_unassigned_persons,
              tool_list_persons_not_in_rfp,
              tool_find_persons_by_skills,
              tool_avg_project_duration,
              tool_find_available_persons,
              tool_pipeline_skill_gaps,
              tool_explain_match
              ])

TOOLS_BY_NAME = {
    "tool_list_rfps": tool_list_rfps,
    "tool_match_rfp": tool_match_rfp,
    "tool_assign_person": tool_assign_person,
    "tool_list_persons": tool_list_persons,
    "tool_get_person_graph": tool_get_person_graph,
    "tool_search_person":tool_search_person,
    "tool_list_assigned_people": tool_list_assigned_people,
    "tool_list_unassigned_persons": tool_list_unassigned_persons,
    "tool_list_persons_not_in_rfp": tool_list_persons_not_in_rfp,
    "tool_find_persons_by_skills": tool_find_persons_by_skills,
    "tool_avg_project_duration": tool_avg_project_duration,
    "tool_find_available_persons": tool_find_available_persons,
    "tool_pipeline_skill_gaps": tool_pipeline_skill_gaps,
    "tool_explain_match":tool_explain_match
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
    return {"messages": messages, "query_type": query_type}


def call_tools_and_answer(state: RouterState) -> Dict:
    # bierzemy historię z routera
    history = state["messages"][:]
    qt = state.get("query_type") or "unknown"
    system_msg = (
        "Jesteś asystentem TalentMatch.\n"
        f"Typ zapytania: {qt}\n\n"
        "ZASADY:\n"
        "- NIE wywołuj narzędzi modyfikujących dane (ASSIGN, UPDATE, DELETE), "
        "jeśli nie masz jawnie podanych wszystkich wymaganych parametrów.\n"
        "- Jeśli brakuje parametrów: zapytaj użytkownika i CZEKAJ.\n"
        "- Parametry wymagane do przypisania osoby:\n"
        "  role, allocation (0-1), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD).\n"
        "- Nie zgaduj wartości.\n"
    )

    messages_for_llm = [("system", system_msg)] + history
    while True:
        ai_msg = agent_llm.invoke(messages_for_llm)
        messages_for_llm.append(ai_msg)

        tool_calls = getattr(ai_msg, "tool_calls", None)
        if not tool_calls:
            break

        for tc in tool_calls:
            name = tc["name"]
            args = tc["args"]
            tool_id = tc["id"]
            tool = TOOLS_BY_NAME.get(name)
            if tool is None:
                tool_result = f"Nieznane narzędzie: {name}"
            else:
                try:
                    tool_result = tool.invoke(args)
                except Exception as e:
                    tool_result = {
                        "error": f"{type(e).__name__}: {e}",
                        "tool": name,
                        "args": args,
                    }
                    print(tool_result)

            tool_msg = ToolMessage(
                content=json.dumps(tool_result, ensure_ascii=False),
                tool_call_id=tool_id,
            )
            messages_for_llm.append(tool_msg)

    new_messages = history + messages_for_llm[len(history) + 1:]
    return {"messages": new_messages}
