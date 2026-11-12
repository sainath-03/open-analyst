"""Natural language -> PostgreSQL using LangChain and the semantic view YAML."""
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, SEMANTIC_VIEW_PATH

load_dotenv()

SYSTEM = """You are an expert PostgreSQL analyst. Convert the user's question into ONE read-only SQL query.

Use ONLY the tables, columns, metrics, filters and relationships in this semantic view
(database olist, schema public). Metric `expr` values are aggregate expressions; dimensions
are plain columns. Follow the join relationships exactly.

{semantic_view}

Rules:
- Output only the SQL, no explanation. SELECT / WITH statements only.
- PostgreSQL dialect. Use table aliases only if unambiguous.
- Add LIMIT 100 unless the question asks for an aggregate that returns few rows.
"""

prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("human", "{question}")])


def _clean(sql: str) -> str:
    sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", sql.strip(), flags=re.I)
    return sql.strip()


def _assert_read_only(sql: str) -> None:
    if not re.match(r"^\s*(select|with)\b", sql, re.I) or re.search(
        r"\b(insert|update|delete|drop|alter|truncate|create|grant)\b", sql, re.I
    ):
        raise ValueError(f"Refusing non read-only SQL:\n{sql}")


def build_llm():
    return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)


def build_chain():
    llm = build_llm()
    semantic_view = Path(SEMANTIC_VIEW_PATH).read_text()
    return prompt.partial(semantic_view=semantic_view) | llm | StrOutputParser()


def generate_sql(question: str) -> str:
    sql = _clean(build_chain().invoke({"question": question}))
    _assert_read_only(sql)
    return sql


if __name__ == "__main__":
    print(generate_sql(" ".join(sys.argv[1:]) or "How many orders were placed per month in 2017?"))
