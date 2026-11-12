DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analyst_ro') THEN
    CREATE ROLE analyst_ro LOGIN PASSWORD 'ro_secret';
  END IF;
END $$;
GRANT CONNECT ON DATABASE olist TO analyst_ro;
GRANT USAGE ON SCHEMA public TO analyst_ro;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM analyst_ro;
GRANT SELECT ON orders, customers, order_items, order_payments, order_reviews, products, product_categories, sellers TO analyst_ro;
ALTER ROLE analyst_ro SET statement_timeout = '15s';
ALTER ROLE analyst_ro SET default_transaction_read_only = on;
