import psycopg
from psycopg.rows import dict_row

from app.config import READONLY_DATABASE_URL


def run_query(sql: str, max_rows: int = 500) -> dict:
    """Execute SQL in a read-only transaction with a statement timeout."""
    with psycopg.connect(READONLY_DATABASE_URL, row_factory=dict_row) as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = '15s'")
            cur.execute(sql)
            columns = [c.name for c in cur.description]
            rows = cur.fetchmany(max_rows)
    return {"columns": columns, "rows": rows, "row_count": len(rows)}
