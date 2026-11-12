"""AST-based SQL guardrails (sqlglot): one read-only SELECT over allowed tables."""
import sqlglot
from sqlglot import exp

from app.config import ALLOWED_TABLES

_FORBIDDEN = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter,
              exp.Command, exp.Merge, exp.Copy, exp.TruncateTable)


def validate_sql(sql: str) -> str:
    """Return normalized SQL or raise ValueError describing the problem."""
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"SQL syntax error: {e}")
    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise ValueError("Exactly one SQL statement is allowed")
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.With)) and not tree.find(exp.Select):
        raise ValueError("Only SELECT queries are allowed")
    if isinstance(tree, _FORBIDDEN) or tree.find(*_FORBIDDEN):
        raise ValueError("Only read-only queries are allowed")
    if tree.find(exp.Into):
        raise ValueError("SELECT INTO is not allowed")
    ctes = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    for t in tree.find_all(exp.Table):
        name = t.name.lower()
        if name not in ctes and name not in ALLOWED_TABLES:
            raise ValueError(f"Table '{t.name}' is not in the semantic view")
    return tree.sql(dialect="postgres")
