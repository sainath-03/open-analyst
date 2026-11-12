from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.db import run_query
from app.graph import ask
from app.validator import validate_sql
from app.sql_generator import generate_sql

app = FastAPI(title="open-analyst", description="Natural language to SQL over the Olist dataset")


class Question(BaseModel):
    question: str = Field(..., min_length=3, examples=["Top 5 product categories by GMV"])


class SQLResponse(BaseModel):
    question: str
    sql: str


class QueryResponse(SQLResponse):
    columns: list[str]
    rows: list[dict]
    row_count: int


class SQLRequest(BaseModel):
    sql: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-sql", response_model=SQLResponse)
def generate(req: Question):
    """Question -> SQL (not executed)."""
    try:
        return SQLResponse(question=req.question, sql=validate_sql(generate_sql(req.question)))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/query", response_model=QueryResponse)
def query(req: Question):
    """Question -> SQL -> validate -> execute (self-correcting, max retries) -> rows."""
    state = ask(req.question)
    if state.get("error") or not state.get("result"):
        raise HTTPException(status_code=400, detail={"error": state.get("error") or "No result", "sql": state.get("sql")})
    return QueryResponse(question=req.question, sql=state["sql"], **state["result"])


@app.post("/execute")
def execute(req: SQLRequest):
    """Run a given SQL string after AST validation (read-only, allowed tables)."""
    try:
        return run_query(validate_sql(req.sql))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Query failed")
