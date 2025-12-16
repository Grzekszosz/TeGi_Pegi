from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class RFPRequirement(BaseModel):
    skill_name: str
    min_proficiency: str
    is_mandatory: bool
    preferred_certifications: List[str] = Field(default_factory=list)

class RFPModel(BaseModel):
    id: str
    title: str
    client: str
    description: str
    project_type: str
    duration_months: int
    team_size: int
    budget_range: str
    start_date: str
    requirements: List[RFPRequirement]
    location: str
    remote_allowed: bool

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Extract a single RFP into strict JSON matching the given schema. "
     "If a field is missing, infer carefully from text or use best-effort defaults. "
     "remote_allowed: true if remote work allowed, false if not allowed."),
    ("user",
     "RFP TEXT:\n{rfp_text}\n\nReturn ONLY JSON.")
])

def extract_rfp_json(rfp_text: str, model: str = "gpt-4o-mini") -> RFPModel:
    llm = ChatOpenAI(model=model, temperature=0)
    structured = llm.with_structured_output(RFPModel)
    chain = PROMPT | structured
    return chain.invoke({"rfp_text": rfp_text})
