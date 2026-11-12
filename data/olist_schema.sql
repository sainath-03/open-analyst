DROP TABLE IF EXISTS orders, customers, order_items, order_payments, order_reviews, products, product_categories, sellers CASCADE;
CREATE TABLE customers (customer_id text, customer_unique_id text, customer_zip_code_prefix text, customer_city text, customer_state text);
CREATE TABLE orders (order_id text, customer_id text, order_status text, order_purchase_timestamp timestamp, order_approved_at timestamp, order_delivered_carrier_date timestamp, order_delivered_customer_date timestamp, order_estimated_delivery_date timestamp);
CREATE TABLE order_items (order_id text, order_item_id int, product_id text, seller_id text, shipping_limit_date timestamp, price numeric(10,2), freight_value numeric(10,2));
CREATE TABLE order_payments (order_id text, payment_sequential int, payment_type text, payment_installments int, payment_value numeric(10,2));
CREATE TABLE order_reviews (review_id text, order_id text, review_score int, review_comment_title text, review_comment_message text, review_creation_date timestamp, review_answer_timestamp timestamp);
CREATE TABLE products (product_id text, product_category_name text, product_name_lenght int, product_description_lenght int, product_photos_qty int, product_weight_g int, product_length_cm int, product_height_cm int, product_width_cm int);
CREATE TABLE product_categories (product_category_name text, product_category_name_english text);
CREATE TABLE sellers (seller_id text, seller_zip_code_prefix text, seller_city text, seller_state text);
