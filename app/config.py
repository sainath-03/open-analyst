import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://analyst:secret@localhost:5432/olist")
SEMANTIC_VIEW_PATH = os.getenv("SEMANTIC_VIEW_PATH", "data/E_commerce.yaml")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:12b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# Least-privilege role used by the API to run generated SQL (see data/readonly_role.sql)
READONLY_DATABASE_URL = os.getenv("READONLY_DATABASE_URL", "postgresql://analyst_ro:ro_secret@localhost:5432/olist")
ALLOWED_TABLES = {"orders", "customers", "order_items", "order_payments", "order_reviews", "products", "product_categories", "sellers"}
MAX_SQL_RETRIES = int(os.getenv("MAX_SQL_RETRIES", "2"))
