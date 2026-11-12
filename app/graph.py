"""LangGraph pipeline: generate -> validate -> execute, with self-correcting retries."""
from typing import Optional, TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from app.config import MAX_SQL_RETRIES
from app.db import run_query
from pathlib import Path

from app.config import SEMANTIC_VIEW_PATH
from app.sql_generator import SYSTEM, _clean, build_chain, build_llm
from app.validator import validate_sql

REPAIR = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human",
     "The PostgreSQL query below failed.\n\nQuestion: {question}\n\nSQL:\n{sql}\n\n"
     "Error:\n{error}\n\nFix it using only tables/columns from the semantic view. "
     "Output only the corrected SQL.")
])


class State(TypedDict, total=False):
    question: str
    sql: str
    error: Optional[str]
    result: Optional[dict]
    attempts: int


def generate(state: State) -> State:
    return {"sql": _clean(build_chain().invoke({"question": state["question"]})), "attempts": 0, "error": None}


def validate(state: State) -> State:
    try:
        return {"sql": validate_sql(state["sql"]), "error": None}
    except ValueError as e:
        return {"error": str(e)}


def execute(state: State) -> State:
    try:
        return {"result": run_query(state["sql"]), "error": None}
    except Exception as e:
        return {"error": str(e).strip().splitlines()[0] if str(e).strip() else repr(e)}


def repair(state: State) -> State:
    chain = REPAIR.partial(semantic_view=Path(SEMANTIC_VIEW_PATH).read_text()) | build_llm() | StrOutputParser()
    fixed = chain.invoke({"question": state["question"], "sql": state["sql"], "error": state["error"]})
    return {"sql": _clean(fixed), "attempts": state.get("attempts", 0) + 1}


def after_validate(state: State) -> str:
    if not state.get("error"):
        return "execute"
    return "repair" if state.get("attempts", 0) < MAX_SQL_RETRIES else END


def after_execute(state: State) -> str:
    if not state.get("error"):
        return END
    return "repair" if state.get("attempts", 0) < MAX_SQL_RETRIES else END


def build_graph():
    g = StateGraph(State)
    g.add_node("generate", generate)
    g.add_node("validate", validate)
    g.add_node("execute", execute)
    g.add_node("repair", repair)
    g.set_entry_point("generate")
    g.add_edge("generate", "validate")
    g.add_conditional_edges("validate", after_validate, {"execute": "execute", "repair": "repair", END: END})
    g.add_conditional_edges("execute", after_execute, {"repair": "repair", END: END})
    g.add_edge("repair", "validate")
    return g.compile()


_graph = None


def ask(question: str) -> State:
    global _graph
    _graph = _graph or build_graph()
    return _graph.invoke({"question": question})
