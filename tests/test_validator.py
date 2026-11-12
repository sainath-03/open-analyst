import pytest

from app.validator import validate_sql


def test_allows_select_with_join_and_cte():
    sql = "WITH x AS (SELECT order_id FROM orders) SELECT COUNT(*) FROM x JOIN order_items oi ON oi.order_id = x.order_id"
    assert validate_sql(sql)


@pytest.mark.parametrize("bad", [
    "DROP TABLE orders",
    "DELETE FROM orders",
    "UPDATE orders SET order_status='x'",
    "SELECT 1; DROP TABLE orders",
    "SELECT * FROM pg_user",
    "SELECT * FROM information_schema.tables",
    "SELECT * INTO newt FROM orders",
    "SELEC oops",
])
def test_rejects(bad):
    with pytest.raises(ValueError):
        validate_sql(bad)


def test_column_named_like_keyword_is_fine():
    assert validate_sql("SELECT order_purchase_timestamp AS created_at FROM orders")
